import pytest

from shvatka.core.views.game import (
    Event,
    GameLogEvent,
    GameLogType,
    GameViewPreparer,
    SendPuzzle,
    WrongKey,
)
from shvatka.tasks import notify_orgs, show_game, write_game_log
from shvatka.views import (
    ComplexGameLogWriter,
    ComplexGameViewPreparer,
    ComplexOrgNotifier,
    ComplexView,
)
from tests.mocks.nursery import FakeNursery


class RecordingPreparer(GameViewPreparer):
    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[tuple] = []
        self.fail = fail

    async def prepare_game_view(self, game, teams, orgs, dao) -> None:
        self.calls.append((game, list(teams), list(orgs), dao))
        if self.fail:
            raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_one_job_for_the_whole_request() -> None:
    nursery = FakeNursery()
    tasks = [
        WrongKey(key="key", input_container=None),
        SendPuzzle(team="team", level="level"),
    ]

    await ComplexView(nursery).show(tasks)

    assert len(nursery.spawned) == 1, "one job, so one request's messages keep their order"
    job, kwargs = nursery.spawned[0]
    assert job is show_game
    assert list(kwargs["tasks"]) == tasks


@pytest.mark.asyncio
async def test_nothing_to_show_starts_no_job() -> None:
    nursery = FakeNursery()

    await ComplexView(nursery).show([])

    assert nursery.spawned == []


@pytest.mark.asyncio
async def test_orgs_are_told_in_the_background() -> None:
    nursery = FakeNursery()
    event = Event(orgs_list=[])

    await ComplexOrgNotifier(nursery).notify(event)

    job, kwargs = nursery.spawned[0]
    assert job is notify_orgs
    assert kwargs["event"] is event


@pytest.mark.asyncio
async def test_game_log_is_written_in_the_background() -> None:
    nursery = FakeNursery()
    event = GameLogEvent(type=GameLogType.GAME_FINISHED)

    await ComplexGameLogWriter(nursery).log(event)

    job, kwargs = nursery.spawned[0]
    assert job is write_game_log
    assert kwargs["log_event"] is event


@pytest.mark.asyncio
async def test_preparer_prepares_both() -> None:
    bot = RecordingPreparer()
    web = RecordingPreparer()
    preparer = ComplexGameViewPreparer(bot, web)

    await preparer.prepare_game_view("game", iter(["t1"]), iter(["o1"]), "dao")

    assert bot.calls == [("game", ["t1"], ["o1"], "dao")]
    assert web.calls == [("game", ["t1"], ["o1"], "dao")]


@pytest.mark.asyncio
async def test_preparer_web_runs_even_if_bot_fails() -> None:
    bot = RecordingPreparer(fail=True)
    web = RecordingPreparer()
    preparer = ComplexGameViewPreparer(bot, web)

    await preparer.prepare_game_view("game", iter(["t1"]), iter(["o1"]), "dao")

    assert bot.calls
    assert web.calls == [("game", ["t1"], ["o1"], "dao")]
