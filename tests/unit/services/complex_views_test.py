import pytest

from shvatka.core.views.game import (
    Event,
    GameLogEvent,
    GameLogType,
    GameViewPreparer,
    SendPuzzle,
    ShowTasks,
)
from shvatka.tgbot.tasks import NurseryViewSender, show_game
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


class RecordingHalf:
    def __init__(self, journal: list[str], name: str, *, fail: bool = False) -> None:
        self.journal = journal
        self.name = name
        self.fail = fail

    async def show(self, tasks) -> None:
        self._record(list(tasks))

    async def notify(self, event) -> None:
        self._record(event)

    async def log(self, log_event) -> None:
        self._record(log_event)

    def _record(self, what) -> None:
        self.journal.append(f"{self.name}: {what}")
        if self.fail:
            raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_one_job_for_the_whole_request() -> None:
    nursery = FakeNursery()
    tasks = ShowTasks(view=[SendPuzzle(team="team", level="level")])

    await NurseryViewSender(nursery).show_later(tasks)

    assert len(nursery.spawned) == 1, "one job, so one request's messages keep their order"
    job, kwargs = nursery.spawned[0]
    assert job is show_game
    assert kwargs["tasks"] is tasks


@pytest.mark.asyncio
async def test_nothing_to_show_starts_no_job() -> None:
    nursery = FakeNursery()

    await NurseryViewSender(nursery).show_later(ShowTasks())

    assert nursery.spawned == []


@pytest.mark.asyncio
async def test_view_shows_on_both_edges_site_first() -> None:
    journal: list[str] = []
    view = ComplexView(RecordingHalf(journal, "bot"), RecordingHalf(journal, "web"))

    await view.show([SendPuzzle(team="team", level="level")])

    assert [entry.split(":")[0] for entry in journal] == ["web", "bot"]


@pytest.mark.asyncio
async def test_a_broken_push_does_not_cost_the_chat_its_message() -> None:
    journal: list[str] = []
    view = ComplexView(RecordingHalf(journal, "bot"), RecordingHalf(journal, "web", fail=True))

    await view.show([SendPuzzle(team="team", level="level")])

    assert [entry.split(":")[0] for entry in journal] == ["web", "bot"]


@pytest.mark.asyncio
async def test_a_failing_chat_is_left_to_the_caller_to_retry() -> None:
    journal: list[str] = []
    view = ComplexView(RecordingHalf(journal, "bot", fail=True), RecordingHalf(journal, "web"))

    with pytest.raises(RuntimeError):
        await view.show([SendPuzzle(team="team", level="level")])


@pytest.mark.asyncio
async def test_orgs_and_log_go_to_both_edges() -> None:
    journal: list[str] = []
    notifier = ComplexOrgNotifier(RecordingHalf(journal, "bot"), RecordingHalf(journal, "web"))
    writer = ComplexGameLogWriter(RecordingHalf(journal, "bot"), RecordingHalf(journal, "web"))

    await notifier.notify(Event(orgs_list=[]))
    await writer.log(GameLogEvent(type=GameLogType.GAME_FINISHED))

    assert [entry.split(":")[0] for entry in journal] == ["web", "bot", "web", "bot"]


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
