import logging
import secrets

from shvatka.core.interfaces.dal.email import (
    EmailAccountDao,
    EmailConfirmationStore,
    EmailRegistrar,
    EmailConfirmer,
)
from shvatka.core.interfaces.hasher import PasswordHasher
from shvatka.core.interfaces.mail import EmailSender
from shvatka.core.models import dto
from shvatka.core.utils import exceptions
from shvatka.core.utils.input_validation import validate_email

logger = logging.getLogger(__name__)

CODE_LEN = 6


def _normalize_or_raise(email: str) -> str:
    normalized = validate_email(email)
    if normalized is None:
        raise exceptions.EmailInvalid(text=f"invalid email {email}")
    return normalized


def _generate_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(CODE_LEN))


async def register_by_email(
    email: str,
    password: str,
    dao: EmailRegistrar,
    hasher: PasswordHasher,
    store: EmailConfirmationStore,
    sender: EmailSender,
) -> dto.Player:
    """Create a brand-new player identified by email and send a confirmation code."""
    email = _normalize_or_raise(email)
    if await dao.is_email_occupied(email):
        raise exceptions.EmailAlreadyExist(text=f"email {email} already occupied")
    player = await dao.create_player_for_email(email, hasher.hash(password))
    await dao.commit()
    await _send_new_code(email, player.id, store, sender)
    return player


async def add_email_to_player(
    player: dto.Player,
    email: str,
    password: str | None,
    dao: EmailRegistrar,
    hasher: PasswordHasher,
    store: EmailConfirmationStore,
    sender: EmailSender,
) -> None:
    """Attach an email to an already existing player (e.g. a telegram user)."""
    email = _normalize_or_raise(email)
    if await dao.is_email_occupied(email):
        raise exceptions.EmailAlreadyExist(text=f"email {email} already occupied")
    if password is not None:
        await dao.set_password_if_absent(player, hasher.hash(password))
    await dao.add_email_to_player(player, email)
    await dao.commit()
    await _send_new_code(email, player.id, store, sender)


async def confirm_email(
    email: str,
    code: str,
    dao: EmailConfirmer,
    store: EmailConfirmationStore,
) -> None:
    email = _normalize_or_raise(email)
    saved = await store.get_code(email)
    if saved is None or not secrets.compare_digest(saved.code, code.strip()):
        raise exceptions.EmailConfirmationCodeInvalid(text=f"wrong code for {email}")
    await dao.set_verified(email)
    await dao.commit()
    await store.remove_code(email)


async def resend_confirmation(
    email: str,
    dao: EmailAccountDao,
    store: EmailConfirmationStore,
    sender: EmailSender,
) -> None:
    email = _normalize_or_raise(email)
    account = await dao.get_by_email(email)
    if account is None:
        raise exceptions.EmailNotFound(text=f"email {email} not found")
    if account.is_verified:
        return
    await _send_new_code(email, account.player_id, store, sender)


async def _send_new_code(
    email: str,
    player_id: int,
    store: EmailConfirmationStore,
    sender: EmailSender,
) -> None:
    code = _generate_code()
    await store.save_code(email, code, player_id)
    await sender.send_confirmation_code(email, code)
    logger.info("confirmation code sent to email of player %s", player_id)
