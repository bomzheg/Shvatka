import pytest

from shvatka.core.models import dto
from shvatka.core.models.enums.chat_type import ChatType
from shvatka.core.views.team import PlayerJoinedTeam, PlayerLeftTeam
from shvatka.tgbot.views.team import BotTeamNotifier


def _player(id_: int, username: str) -> dto.Player:
    return dto.Player(id=id_, can_be_author=False, is_dummy=False, username=username)


def _team(captain: dto.Player | None = None, *, with_chat: bool = True) -> dto.Team:
    chat = dto.Chat(tg_id=-100, type=ChatType.group, title="t") if with_chat else None
    return dto.Team(
        id=1,
        name="Gryffindor",
        captain=captain,
        is_dummy=not with_chat,
        description=None,
        chat=chat,
    )


def test_joined_by_self() -> None:
    harry = _player(1, "harry")
    event = PlayerJoinedTeam(team=_team(harry), player=harry, inviter=harry)
    assert event.by_self
    assert "вступил" in (BotTeamNotifier._render(event) or "")


def test_joined_by_captain() -> None:
    harry = _player(1, "harry")
    ron = _player(2, "ron")
    event = PlayerJoinedTeam(team=_team(harry), player=ron, inviter=harry)
    assert not event.by_self
    text = BotTeamNotifier._render(event) or ""
    assert "добавлен" in text
    assert "harry" in text


def test_left_by_self() -> None:
    ron = _player(2, "ron")
    event = PlayerLeftTeam(team=_team(), player=ron, remover=ron)
    assert event.by_self
    assert "вышел" in (BotTeamNotifier._render(event) or "")


def test_left_by_captain() -> None:
    harry = _player(1, "harry")
    ron = _player(2, "ron")
    event = PlayerLeftTeam(team=_team(harry), player=ron, remover=harry)
    assert not event.by_self
    text = BotTeamNotifier._render(event) or ""
    assert "удалён" in text
    assert "harry" in text


@pytest.mark.asyncio
async def test_no_notify_without_chat() -> None:
    sent: list = []

    class _Bot:
        async def send_message(self, **kwargs):
            sent.append(kwargs)

    ron = _player(2, "ron")
    notifier = BotTeamNotifier(bot=_Bot())
    await notifier.notify(PlayerLeftTeam(team=_team(with_chat=False), player=ron, remover=ron))
    assert sent == []
