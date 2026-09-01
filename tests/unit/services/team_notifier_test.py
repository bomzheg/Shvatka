import pytest

from shvatka.core.models import dto
from shvatka.core.models.enums.chat_type import ChatType
from shvatka.core.views.team import CaptainChanged, PlayerJoinedTeam, PlayerLeftTeam
from shvatka.tgbot.views.team import BotTeamNotifier, render_leave_confirmation


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
    event = PlayerJoinedTeam(team=_team(harry), actor=harry, invited=harry)
    assert event.by_self
    assert "вступил" in (BotTeamNotifier._render(event) or "")


def test_joined_by_captain() -> None:
    harry = _player(1, "harry")
    ron = _player(2, "ron")
    event = PlayerJoinedTeam(team=_team(harry), actor=harry, invited=ron)
    assert not event.by_self
    text = BotTeamNotifier._render(event) or ""
    assert "добавлен" in text
    assert "harry" in text


def test_left_by_self() -> None:
    ron = _player(2, "ron")
    event = PlayerLeftTeam(team=_team(), actor=ron, removed=ron)
    assert event.by_self
    assert "вышел" in (BotTeamNotifier._render(event) or "")


def test_left_by_someone_else() -> None:
    harry = _player(1, "harry")
    ron = _player(2, "ron")
    event = PlayerLeftTeam(team=_team(harry), actor=harry, removed=ron)
    assert not event.by_self
    text = BotTeamNotifier._render(event) or ""
    assert "удалён" in text
    assert "harry" in text
    # the remover is not necessarily the captain: a teammate with the right to
    # manage players, or an engine admin, may have done it
    assert "капитан" not in text


def test_leave_confirmation_in_private() -> None:
    ron = _player(2, "ron")
    text = render_leave_confirmation(ron, _team(), chat_id=ron.id, private=True)
    assert text == "Ты вышел из команды Gryffindor"


def test_leave_confirmation_in_group_names_the_player() -> None:
    ron = _player(2, "ron")
    text = render_leave_confirmation(ron, _team(), chat_id=-200, private=False)
    # a plain message in a group has to say who left, «ты» tells nobody anything
    assert text is not None
    assert "ron" in text
    assert "Ты" not in text
    assert "Gryffindor" in text


def test_no_leave_confirmation_in_team_chat() -> None:
    ron = _player(2, "ron")
    # BotTeamNotifier already announces the leave there, no need to say it twice
    assert render_leave_confirmation(ron, _team(), chat_id=-100, private=False) is None


def test_captain_changed_by_old_captain() -> None:
    harry = _player(1, "harry")
    ron = _player(2, "ron")
    event = CaptainChanged(team=_team(ron), actor=harry, new_captain=ron, old_captain=harry)
    assert event.by_old_captain
    text = BotTeamNotifier._render(event) or ""
    assert "капитан" in text
    assert "ron" in text
    # the handover was the old captain's own doing — no need to name them again
    assert "harry" not in text


def test_captain_changed_by_admin() -> None:
    harry = _player(1, "harry")
    ron = _player(2, "ron")
    admin = _player(3, "dumbledore")
    event = CaptainChanged(team=_team(ron), actor=admin, new_captain=ron, old_captain=harry)
    assert not event.by_old_captain
    text = BotTeamNotifier._render(event) or ""
    assert "ron" in text
    assert "dumbledore" in text


def test_captain_changed_for_team_without_captain() -> None:
    ron = _player(2, "ron")
    admin = _player(3, "dumbledore")
    event = CaptainChanged(team=_team(ron), actor=admin, new_captain=ron, old_captain=None)
    assert not event.by_old_captain
    assert "ron" in (BotTeamNotifier._render(event) or "")


class _Tagger:
    def __init__(self) -> None:
        self.synced: list = []

    async def sync(self, player: dto.Player, team: dto.Team | None) -> None:
        self.synced.append((player, team))


@pytest.mark.asyncio
async def test_no_notify_without_chat() -> None:
    sent: list = []

    class _Bot:
        async def send_message(self, **kwargs) -> None:
            sent.append(kwargs)

    ron = _player(2, "ron")
    notifier = BotTeamNotifier(bot=_Bot(), tagger=_Tagger())
    await notifier.notify(PlayerLeftTeam(team=_team(with_chat=False), actor=ron, removed=ron))
    assert sent == []


@pytest.mark.asyncio
async def test_tag_synced_even_without_team_chat() -> None:
    # the tag lives in a public chat, the team chat has nothing to do with it
    ron = _player(2, "ron")
    tagger = _Tagger()
    notifier = BotTeamNotifier(bot=None, tagger=tagger)
    team = _team(with_chat=False)

    await notifier.notify(PlayerJoinedTeam(team=team, actor=ron, invited=ron))
    await notifier.notify(PlayerLeftTeam(team=team, actor=ron, removed=ron))

    assert [(ron, team), (ron, None)] == tagger.synced
