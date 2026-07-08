import logging
import secrets
from dataclasses import dataclass
from datetime import timedelta

from shvatka.common.url_factory import UrlFactory
from shvatka.core.interfaces.dal.email import (
    EmailAccountDao,
    EmailDao,
    EmailConfirmationStore,
    UsernameOccupiedChecker,
)
from shvatka.core.interfaces.hasher import PasswordHasher
from shvatka.core.interfaces.mail import EmailSender
from shvatka.core.interfaces.one_time_token import OneTimeTokenCreator
from shvatka.core.interfaces.rate_limiter import RateLimiter
from shvatka.core.models import dto
from shvatka.core.utils import exceptions
from shvatka.core.utils.input_validation import validate_email, validate_new_username

logger = logging.getLogger(__name__)

CODE_LEN = 6
FORGOT_PASSWORD_COOLDOWN = timedelta(minutes=2)


@dataclass
class EmailRegisterInteractor:
    dao: EmailDao
    player_dao: UsernameOccupiedChecker
    hasher: PasswordHasher
    store: EmailConfirmationStore
    sender: EmailSender

    async def __call__(self, username: str, email: str, password: str) -> dto.Player:
        """Create a brand-new player identified by email and send a confirmation code."""
        email = normalize_email_or_raise(email)
        validated_username = validate_new_username(username)
        if validated_username is None:
            raise exceptions.PlayerInvalidUsername(text=f"invalid username {username}")
        if await self.player_dao.is_username_occupied(validated_username):
            raise exceptions.PlayerUsernameOccupied(text=f"username {validated_username} occupied")
        if await self.dao.is_email_occupied(email):
            raise exceptions.EmailAlreadyExist(text=f"email {email} already occupied")
        player = await self.dao.create_player_for_email(
            username=validated_username,
            email=email,
            hashed_password=self.hasher.hash(password),
        )
        await self.dao.commit()
        await send_new_code(email, player.id, self.store, self.sender)
        return player


@dataclass
class EmailLinkInteractor:
    dao: EmailDao
    store: EmailConfirmationStore
    sender: EmailSender

    async def __call__(self, player: dto.Player, email: str) -> None:
        """Attach an email to an already existing player (e.g. a telegram user)."""
        email = normalize_email_or_raise(email)
        if await self.dao.is_email_occupied(email):
            raise exceptions.EmailAlreadyExist(text=f"email {email} already occupied")
        await self.dao.add_email_to_player(player, email)
        await self.dao.commit()
        await send_new_code(email, player.id, self.store, self.sender)


@dataclass
class EmailConfirmInteractor:
    dao: EmailDao
    store: EmailConfirmationStore

    async def __call__(self, email: str, code: str) -> None:
        email = normalize_email_or_raise(email)
        saved = await self.store.get_code(email)
        if saved is None or not secrets.compare_digest(saved.code, code.strip()):
            raise exceptions.EmailConfirmationCodeInvalid(text=f"wrong code for {email}")
        await self.dao.set_verified(email)
        await self.dao.commit()
        await self.store.remove_code(email)


@dataclass
class EmailResendInteractor:
    dao: EmailDao
    store: EmailConfirmationStore
    sender: EmailSender

    async def __call__(self, email: str) -> None:
        email = normalize_email_or_raise(email)
        account = await self.dao.get_by_email(email)
        if account is None:
            raise exceptions.EmailNotFound(text=f"email {email} not found")
        if account.is_verified:
            return
        await send_new_code(email, account.player_id, self.store, self.sender)


@dataclass
class ForgotPasswordInteractor:
    dao: EmailAccountDao
    limiter: RateLimiter
    token_creator: OneTimeTokenCreator
    sender: EmailSender
    url_factory: UrlFactory

    async def __call__(self, email: str) -> None:
        email = normalize_email_or_raise(email)
        try:
            player = await self.dao.find_verified_player_by_email(email)
        except exceptions.EmailNotVerified:
            logger.info("forgot password requested for email without a verified account")
            return
        allowed = await self.limiter.is_allowed(
            f"forgot_password:{player.id}", FORGOT_PASSWORD_COOLDOWN
        )
        if not allowed:
            raise exceptions.RateLimitExceeded(
                text=f"forgot password rate limited for player {player.id}"
            )
        token = await self.token_creator.save_new_token(dct={"player_id": player.id})
        url = self.url_factory.get_otl(token)
        await self.sender.send_one_time_link(email, url)


def normalize_email_or_raise(email: str) -> str:
    normalized = validate_email(email)
    if normalized is None:
        raise exceptions.EmailInvalid(text=f"invalid email {email}")
    return normalized


def generate_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(CODE_LEN))


async def send_new_code(
    email: str,
    player_id: int,
    store: EmailConfirmationStore,
    sender: EmailSender,
) -> None:
    code = generate_code()
    await store.save_code(email, code, player_id)
    await sender.send_confirmation_code(email, code)
    logger.info("confirmation code sent to email of player %s", player_id)
