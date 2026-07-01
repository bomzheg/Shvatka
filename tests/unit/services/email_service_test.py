import pytest

from shvatka.core.models import dto
from shvatka.core.services import email as email_service
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
        self.committed = False
        self._next_player_id = 1

    async def is_email_occupied(self, email: str) -> bool:
        return email in self.accounts

    async def create_player_for_email(self, email: str, hashed_password: str) -> dto.Player:
        player_id = self._next_player_id
        self._next_player_id += 1
        self.passwords[player_id] = hashed_password
        self.accounts[email] = dto.EmailAccount(
            email=email, player_id=player_id, is_verified=False
        )
        return dto.Player(
            id=player_id, can_be_author=False, is_dummy=False, username=f"id{player_id}"
        )

    async def add_email_to_player(self, player: dto.Player, email: str) -> dto.EmailAccount:
        account = dto.EmailAccount(email=email, player_id=player.id, is_verified=False)
        self.accounts[email] = account
        return account

    async def set_verified(self, email: str) -> None:
        self.accounts[email].is_verified = True

    async def set_password_if_absent(self, player: dto.Player, hashed_password: str) -> None:
        self.passwords.setdefault(player.id, hashed_password)

    async def get_by_email(self, email: str) -> dto.EmailAccount | None:
        return self.accounts.get(email)

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

    async def send_confirmation_code(self, email: str, code: str) -> None:
        self.sent.append((email, code))


@pytest.fixture
def deps():
    return FakeEmailDao(), FakeStore(), FakeSender(), FakeHasher()


@pytest.mark.asyncio
async def test_register_normalizes_and_sends_code(deps):
    dao, store, sender, hasher = deps
    player = await email_service.register_by_email(
        " Test@Example.COM ", "pw", dao, hasher, store, sender
    )
    assert player.id == 1
    assert "test@example.com" in dao.accounts
    assert dao.committed
    assert len(sender.sent) == 1
    email, code = sender.sent[0]
    assert email == "test@example.com"
    assert len(code) == email_service.CODE_LEN
    assert code.isdigit()


@pytest.mark.asyncio
async def test_register_rejects_duplicate(deps):
    dao, store, sender, hasher = deps
    await email_service.register_by_email("a@b.com", "pw", dao, hasher, store, sender)
    with pytest.raises(exceptions.EmailAlreadyExist):
        await email_service.register_by_email("a@b.com", "pw", dao, hasher, store, sender)


@pytest.mark.asyncio
async def test_register_rejects_invalid(deps):
    dao, store, sender, hasher = deps
    with pytest.raises(exceptions.EmailInvalid):
        await email_service.register_by_email("not-an-email", "pw", dao, hasher, store, sender)


@pytest.mark.asyncio
async def test_confirm_email_flow(deps):
    dao, store, sender, hasher = deps
    await email_service.register_by_email("a@b.com", "pw", dao, hasher, store, sender)
    code = sender.sent[0][1]

    with pytest.raises(exceptions.EmailConfirmationCodeInvalid):
        await email_service.confirm_email("a@b.com", "000000", dao, store)
    assert not dao.accounts["a@b.com"].is_verified

    await email_service.confirm_email("a@b.com", code, dao, store)
    assert dao.accounts["a@b.com"].is_verified
    assert store.codes.get("a@b.com") is None


@pytest.mark.asyncio
async def test_add_email_to_existing_player(deps):
    dao, store, sender, hasher = deps
    player = dto.Player(id=42, can_be_author=False, is_dummy=False, username="tg_user")
    await email_service.add_email_to_player(
        player, "New@Mail.com", "pw", dao, hasher, store, sender
    )
    assert "new@mail.com" in dao.accounts
    assert dao.accounts["new@mail.com"].player_id == 42
    assert dao.passwords[42] == "hashed:pw"
    assert sender.sent[0][0] == "new@mail.com"
