from collections.abc import Collection
from datetime import timedelta
from types import SimpleNamespace

import pytest

from shvatka.api.utils.push import PushMessage
from shvatka.api.utils.web_input import WebOrgNotifier
from shvatka.core.views.game import LevelUp, NewOrg, LevelTestCompleted


class FakePushSender:
    def __init__(self) -> None:
        self.calls: list[tuple[set[int], PushMessage]] = []

    async def send_to_players(self, player_ids: Collection[int], message: PushMessage) -> None:
        self.calls.append((set(player_ids), message))


def _org(player_id: int):
    return SimpleNamespace(player=SimpleNamespace(id=player_id, name_mention="org"))


@pytest.mark.asyncio
async def test_level_up_pushes_to_all_orgs() -> None:
    sender = FakePushSender()
    notifier = WebOrgNotifier(sender)  # type: ignore[arg-type]
    team = SimpleNamespace(id=7, name="Gryffindor")
    level = SimpleNamespace(db_id=3, name_id="lvl-1", number_in_game=0)
    event = LevelUp(orgs_list=[_org(1), _org(2)], team=team, new_level=level)  # type: ignore[arg-type]

    await notifier.notify(event)

    assert len(sender.calls) == 1
    player_ids, message = sender.calls[0]
    assert player_ids == {1, 2}
    assert "Gryffindor" in message.body
    assert "1" in message.body  # number_in_game + 1
    assert message.data["kind"] == "org_level_up"


@pytest.mark.asyncio
async def test_level_up_uses_name_id_without_number() -> None:
    sender = FakePushSender()
    notifier = WebOrgNotifier(sender)  # type: ignore[arg-type]
    team = SimpleNamespace(id=7, name="Gryffindor")
    level = SimpleNamespace(db_id=3, name_id="secret-lvl", number_in_game=None)
    event = LevelUp(orgs_list=[_org(1)], team=team, new_level=level)  # type: ignore[arg-type]

    await notifier.notify(event)

    _, message = sender.calls[0]
    assert "secret-lvl" in message.body


@pytest.mark.asyncio
async def test_new_org_pushes_to_all_orgs() -> None:
    sender = FakePushSender()
    notifier = WebOrgNotifier(sender)  # type: ignore[arg-type]
    game = SimpleNamespace(id=5, name="My Game")
    new_org = SimpleNamespace(id=9, player=SimpleNamespace(id=42, name_mention="newbie"))
    event = NewOrg(orgs_list=[_org(1), _org(2)], game=game, org=new_org)  # type: ignore[arg-type]

    await notifier.notify(event)

    player_ids, message = sender.calls[0]
    assert player_ids == {1, 2}
    assert "My Game" in message.body
    assert "newbie" in message.body
    assert message.data["kind"] == "new_org"


@pytest.mark.asyncio
async def test_level_test_completed_pushes_to_all_orgs() -> None:
    sender = FakePushSender()
    notifier = WebOrgNotifier(sender)  # type: ignore[arg-type]
    tester = SimpleNamespace(player=SimpleNamespace(id=42, name_mention="tester"))
    suite = SimpleNamespace(level=SimpleNamespace(name_id="lvl-1"), tester=tester)
    result = SimpleNamespace(td=timedelta(minutes=2, seconds=5))
    event = LevelTestCompleted(orgs_list=[_org(1)], suite=suite, result=result)  # type: ignore[arg-type]

    await notifier.notify(event)

    player_ids, message = sender.calls[0]
    assert player_ids == {1}
    assert "tester" in message.body
    assert "2 минут 5 с" in message.body
    assert message.data["kind"] == "level_test_completed"
