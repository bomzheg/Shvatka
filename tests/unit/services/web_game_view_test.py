from collections.abc import Collection
from types import SimpleNamespace

import pytest

from shvatka.api.app.utils.push import PushMessage
from shvatka.api.app.utils.web_input import WebGameView
from shvatka.core.views.game import SendHint, SendPuzzle


class FakePushSender:
    def __init__(self) -> None:
        self.calls: list[tuple[set[int], PushMessage]] = []

    async def send_to_players(self, player_ids: Collection[int], message: PushMessage) -> None:
        self.calls.append((set(player_ids), message))


class FakeCurrentGame:
    def __init__(self, player_ids: Collection[int]) -> None:
        self.player_ids = player_ids

    async def get_team_waivers_by_team(self, team) -> list:
        return [SimpleNamespace(player=SimpleNamespace(id=id_)) for id_ in self.player_ids]


def _view(*player_ids: int) -> tuple[WebGameView, FakePushSender]:
    sender = FakePushSender()
    return WebGameView(sender, FakeCurrentGame(player_ids)), sender


def _team():
    return SimpleNamespace(id=7, name="Gryffindor")


def _level(db_id: int, number_in_game: int | None = 0, last_hint: int = 10):
    return SimpleNamespace(
        db_id=db_id,
        name_id=f"lvl-{db_id}",
        number_in_game=number_in_game,
        is_last_hint=lambda number: number == last_hint,
    )


@pytest.mark.asyncio
async def test_puzzle_pushed_to_voted_players_only() -> None:
    view, sender = _view(1, 2)

    await view.show([SendPuzzle(team=_team(), level=_level(3))])

    player_ids, message = sender.calls[0]
    assert player_ids == {1, 2}
    assert "Gryffindor" in message.body
    assert message.data is not None
    assert message.data["kind"] == "puzzle"


@pytest.mark.asyncio
async def test_level_up_replaces_the_previous_one() -> None:
    """Moving to level 4 must hide the push about moving to level 3."""
    view, sender = _view(1)
    team = _team()

    await view.show(
        [
            SendPuzzle(team=team, level=_level(3, number_in_game=2)),
            SendPuzzle(team=team, level=_level(4, number_in_game=3)),
        ]
    )

    first, second = (message.tag for _, message in sender.calls)
    assert first == second == "level-7"


@pytest.mark.asyncio
async def test_every_hint_of_a_team_shares_one_tag() -> None:
    """The tray keeps the last hint, not the whole history of them."""
    view, sender = _view(1)
    team = _team()
    level = _level(3)

    await view.show(
        [
            SendHint(team=team, hint_number=1, level=level),
            SendHint(team=team, hint_number=2, level=level),
            SendHint(team=team, hint_number=10, level=level),
        ]
    )

    assert {"hint-7"} == {message.tag for _, message in sender.calls}
    *_, (_, last) = sender.calls
    assert last.title == "Последняя подсказка"


@pytest.mark.asyncio
async def test_a_hint_never_replaces_a_level_up() -> None:
    view, sender = _view(1)
    team = _team()
    level = _level(3)

    await view.show(
        [SendPuzzle(team=team, level=level), SendHint(team=team, hint_number=1, level=level)]
    )

    puzzle, hint = (message.tag for _, message in sender.calls)
    assert puzzle != hint
