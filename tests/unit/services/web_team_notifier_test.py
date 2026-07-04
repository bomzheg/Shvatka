from collections.abc import Collection
from types import SimpleNamespace

import pytest

from shvatka.api.utils.push import PushMessage
from shvatka.api.utils.web_input import WebTeamNotifier
from shvatka.core.views.team import PlayerJoinedTeam, PlayerLeftTeam


class FakePushSender:
    def __init__(self) -> None:
        self.calls: list[tuple[set[int], PushMessage]] = []

    async def send_to_players(self, player_ids: Collection[int], message: PushMessage) -> None:
        self.calls.append((set(player_ids), message))


class FakeNotificationDao:
    def __init__(self) -> None:
        self.created: list[dict] = []
        self.commits = 0

    async def create_for_recipients(self, **kwargs) -> None:
        self.created.append(kwargs)

    async def commit(self) -> None:
        self.commits += 1


class FakeTeamPlayersDao:
    def __init__(self, player_ids: list[int]) -> None:
        self._players = [SimpleNamespace(player=SimpleNamespace(id=pid)) for pid in player_ids]

    async def get_players(self, team):
        return self._players


def _player(pid: int, name: str = "player"):
    return SimpleNamespace(id=pid, name_mention=name)


def _team(team_id: int = 7, name: str = "Gryffindor"):
    return SimpleNamespace(id=team_id, name=name)


@pytest.mark.asyncio
async def test_player_joined_persists_and_pushes_to_members() -> None:
    sender = FakePushSender()
    notification_dao = FakeNotificationDao()
    # after join the team has members {10 (existing), 42 (joined)}
    notifier = WebTeamNotifier(notification_dao, FakeTeamPlayersDao([10, 42]), sender)
    event = PlayerJoinedTeam(team=_team(), actor=_player(10, "cap"), invited=_player(42, "newbie"))

    await notifier.notify(event)

    assert notification_dao.commits == 1
    persisted = notification_dao.created[0]
    assert persisted["recipient_ids"] == {10, 42}
    assert persisted["type_"].name == "player_joined_team"
    assert persisted["actor_id"] == 10
    assert persisted["payload"]["player_id"] == 42

    player_ids, message = sender.calls[0]
    assert player_ids == {10, 42}
    assert message.data is not None
    assert message.data["kind"] == "player_joined_team"


@pytest.mark.asyncio
async def test_player_left_persists_to_remaining_members() -> None:
    sender = FakePushSender()
    notification_dao = FakeNotificationDao()
    # after leave only {10} remains; removed player 42 not in the list
    notifier = WebTeamNotifier(notification_dao, FakeTeamPlayersDao([10]), sender)
    event = PlayerLeftTeam(team=_team(), actor=_player(10, "cap"), removed=_player(42, "gone"))

    await notifier.notify(event)

    persisted = notification_dao.created[0]
    assert persisted["recipient_ids"] == {10}
    assert persisted["type_"].name == "player_left_team"
    assert persisted["payload"]["player_id"] == 42


@pytest.mark.asyncio
async def test_no_recipients_no_calls() -> None:
    sender = FakePushSender()
    notification_dao = FakeNotificationDao()
    notifier = WebTeamNotifier(notification_dao, FakeTeamPlayersDao([]), sender)
    event = PlayerLeftTeam(team=_team(), actor=_player(10), removed=_player(42))

    await notifier.notify(event)

    assert notification_dao.created == []
    assert notification_dao.commits == 0
    assert sender.calls == []
