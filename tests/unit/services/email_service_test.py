from datetime import timedelta

import pytest

from shvatka.core.models import dto
from shvatka.core.services import email as email_service
from shvatka.core.services.email import (
    EmailRegisterInteractor,
    EmailLinkInteractor,
    EmailConfirmInteractor,
    EmailResendInteractor,
    ForgotPasswordInteractor,
)
from shvatka.core.utils import exceptions


class FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed:{plain_password}"


class FakeEmailDao:
    def __init__(self) -> None:
        self.accounts: dict[str, dto.EmailAccount] = {}
        self.passwords: dict[int, str] = {}
        self.usernames: set[str] = set()
        self.committed = False
        self._next_player_id = 1

    async def is_email_occupied(self, email: str) -> bool:
        return email in self.accounts

    async def is_username_occupied(self, username: str) -> bool:
        return username in self.usernames

    async def create_player_for_email(
        self, username: str, email: str, hashed_password: str
    ) -> dto.Player:
        player_id = self._next_player_id
        self._next_player_id += 1
        self.passwords[player_id] = hashed_password
        self.usernames.add(username)
        self.accounts[email] = dto.EmailAccount(
            email=email, player_id=player_id, is_verified=False
        )
        return dto.Player(id=player_id, can_be_author=False, is_dummy=False, username=username)

    async def add_email_to_player(self, player: dto.Player, email: str) -> dto.EmailAccount:
        account = dto.EmailAccount(email=email, player_id=player.id, is_verified=False)
        self.accounts[email] = account
        return account

    async def set_verified(self, email: str) -> None:
        self.accounts[email].is_verified = True

    async def get_by_email(self, email: str) -> dto.EmailAccount | None:
        return self.accounts.get(email)

    async def find_verified_player_by_email(self, email: str) -> dto.Player:
        account = self.accounts.get(email)
        if account is None or not account.is_verified:
            raise exceptions.EmailNotVerified(text=f"no verified email {email}")
        return dto.Player(
            id=account.player_id,
            can_be_author=False,
            is_dummy=False,
            username="player",
        )

    async def commit(self) -> None:
        self.committed = True


class FakeStore:
    def __init__(self) -> None:
        self.codes: dict[str, dto.EmailConfirmation] = {}

    async def save_code(self, email: str, code: str, player_id: int) -> None:
        self.codes[email] = dto.EmailConfirmation(email=email, code=code, player_id=player_id)

    async def get_code(self, email: str) -> dto.EmailConfirmation | None:
        return self.codes.get(email)

    async def remove_code(self, email: str) -> None:
        self.codes.pop(email, None)


class FakeSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []
        self.links: list[tuple[str, str]] = []

    async def send_confirmation_code(self, email: str, code: str) -> None:
        self.sent.append((email, code))

    async def send_one_time_link(self, email: str, url: str) -> None:
        self.links.append((email, url))


class FakeLimiter:
    def __init__(self) -> None:
        self.used: set[str] = set()

    async def is_allowed(self, key: str, cooldown: timedelta) -> bool:
        if key in self.used:
            return False
        self.used.add(key)
        return True


class FakeTokenCreator:
    def __init__(self) -> None:
        self.saved: list[dict] = []
        self._next = 1

    async def save_new_token(self, **dct: dict) -> str:
        token = f"token{self._next}"
        self._next += 1
        self.saved.append(dct["dct"])
        return token


@pytest.fixture
def dao() -> FakeEmailDao:
    return FakeEmailDao()


@pytest.fixture
def store() -> FakeStore:
    return FakeStore()


@pytest.fixture
def sender() -> FakeSender:
    return FakeSender()


@pytest.fixture
def register(dao, store, sender) -> EmailRegisterInteractor:
    return EmailRegisterInteractor(
        dao=dao, player_dao=dao, hasher=FakeHasher(), store=store, sender=sender
    )


@pytest.fixture
def link(dao, store, sender) -> EmailLinkInteractor:
    return EmailLinkInteractor(dao=dao, store=store, sender=sender)


@pytest.fixture
def confirm(dao, store) -> EmailConfirmInteractor:
    return EmailConfirmInteractor(dao=dao, store=store)


@pytest.fixture
def resend(dao, store, sender) -> EmailResendInteractor:
    return EmailResendInteractor(dao=dao, store=store, sender=sender)


@pytest.fixture
def limiter() -> FakeLimiter:
    return FakeLimiter()


@pytest.fixture
def token_creator() -> FakeTokenCreator:
    return FakeTokenCreator()


@pytest.fixture
def forgot_password(dao, limiter, token_creator, sender) -> ForgotPasswordInteractor:
    return ForgotPasswordInteractor(
        dao=dao,
        limiter=limiter,
        token_creator=token_creator,
        sender=sender,
        base_url="https://example.com",
    )


@pytest.mark.asyncio
async def test_register_normalizes_and_sends_code(register, dao, sender):
    player = await register(username="harry", email=" Test@Example.COM ", password="pw")
    assert player.id == 1
    assert player.username == "harry"
    assert "test@example.com" in dao.accounts
    assert dao.committed
    assert len(sender.sent) == 1
    email, code = sender.sent[0]
    assert email == "test@example.com"
    assert len(code) == email_service.CODE_LEN
    assert code.isdigit()


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(register):
    await register(username="harry", email="a@b.com", password="pw")
    with pytest.raises(exceptions.EmailAlreadyExist):
        await register(username="ronald", email="a@b.com", password="pw")


@pytest.mark.asyncio
async def test_register_rejects_occupied_username(register):
    await register(username="harry", email="a@b.com", password="pw")
    with pytest.raises(exceptions.PlayerUsernameOccupied):
        await register(username="harry", email="c@d.com", password="pw")


@pytest.mark.asyncio
async def test_register_rejects_invalid_email(register):
    with pytest.raises(exceptions.EmailInvalid):
        await register(username="harry", email="not-an-email", password="pw")


@pytest.mark.asyncio
async def test_register_rejects_invalid_username(register):
    with pytest.raises(exceptions.PlayerInvalidUsername):
        await register(username="a", email="a@b.com", password="pw")


@pytest.mark.asyncio
async def test_confirm_email_flow(register, confirm, dao, store, sender):
    await register(username="harry", email="a@b.com", password="pw")
    code = sender.sent[0][1]

    with pytest.raises(exceptions.EmailConfirmationCodeInvalid):
        await confirm(email="a@b.com", code="000000")
    assert not dao.accounts["a@b.com"].is_verified

    await confirm(email="a@b.com", code=code)
    assert dao.accounts["a@b.com"].is_verified
    assert store.codes.get("a@b.com") is None


@pytest.mark.asyncio
async def test_link_email_to_existing_player(link, dao, sender):
    player = dto.Player(id=42, can_be_author=False, is_dummy=False, username="tg_user")
    await link(player=player, email="New@Mail.com")
    assert "new@mail.com" in dao.accounts
    assert dao.accounts["new@mail.com"].player_id == 42
    assert sender.sent[0][0] == "new@mail.com"


@pytest.mark.asyncio
async def test_resend_sends_new_code_for_unverified(register, resend, sender):
    await register(username="harry", email="a@b.com", password="pw")
    await resend(email="a@b.com")
    assert len(sender.sent) == 2


@pytest.mark.asyncio
async def test_resend_skips_verified(register, confirm, resend, sender):
    await register(username="harry", email="a@b.com", password="pw")
    await confirm(email="a@b.com", code=sender.sent[0][1])
    await resend(email="a@b.com")
    assert len(sender.sent) == 1


@pytest.mark.asyncio
async def test_resend_unknown_email(resend):
    with pytest.raises(exceptions.EmailNotFound):
        await resend(email="nobody@nowhere.com")


@pytest.mark.asyncio
async def test_forgot_password_sends_link_for_verified_email(
    register, confirm, forgot_password, sender, token_creator
):
    await register(username="harry", email="a@b.com", password="pw")
    await confirm(email="a@b.com", code=sender.sent[0][1])

    await forgot_password(email="A@B.com")

    assert token_creator.saved == [{"player_id": 1}]
    assert sender.links == [("a@b.com", "https://example.com/auth/one-time-token?token=token1")]


@pytest.mark.asyncio
async def test_forgot_password_silent_for_unverified_email(register, forgot_password, sender):
    await register(username="harry", email="a@b.com", password="pw")
    await forgot_password(email="a@b.com")
    assert sender.links == []


@pytest.mark.asyncio
async def test_forgot_password_silent_for_unknown_email(forgot_password, sender):
    await forgot_password(email="nobody@nowhere.com")
    assert sender.links == []


@pytest.mark.asyncio
async def test_forgot_password_rejects_invalid_email(forgot_password):
    with pytest.raises(exceptions.EmailInvalid):
        await forgot_password(email="not-an-email")


@pytest.mark.asyncio
async def test_forgot_password_is_rate_limited_per_player(
    register, confirm, forgot_password, sender
):
    await register(username="harry", email="a@b.com", password="pw")
    await confirm(email="a@b.com", code=sender.sent[0][1])

    await forgot_password(email="a@b.com")
    with pytest.raises(exceptions.RateLimitExceeded):
        await forgot_password(email="a@b.com")
    assert len(sender.links) == 1


@pytest.mark.asyncio
async def test_forgot_password_rate_limit_is_shared_across_a_players_emails(
    register, confirm, forgot_password, sender, dao
):
    await register(username="harry", email="a@b.com", password="pw")
    await confirm(email="a@b.com", code=sender.sent[0][1])
    player = dto.Player(id=1, can_be_author=False, is_dummy=False, username="harry")
    await dao.add_email_to_player(player, "second@b.com")
    await dao.set_verified("second@b.com")

    await forgot_password(email="a@b.com")
    with pytest.raises(exceptions.RateLimitExceeded):
        await forgot_password(email="second@b.com")
    assert len(sender.links) == 1


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_does_not_consume_rate_limit(forgot_password, limiter):
    await forgot_password(email="nobody@nowhere.com")
    assert limiter.used == set()
