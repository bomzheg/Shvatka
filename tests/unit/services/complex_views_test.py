import pytest

from shvatka.core.views.game import GameLogWriter, GameLogEvent, GameLogType, GameViewPreparer
from shvatka.main_factory import ComplexGameLogWriter, ComplexGameViewPreparer


class RecordingLogWriter(GameLogWriter):
    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[GameLogEvent] = []
        self.fail = fail

    async def log(self, log_event: GameLogEvent) -> None:
        self.calls.append(log_event)
        if self.fail:
            raise RuntimeError("boom")


class RecordingPreparer(GameViewPreparer):
    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[tuple] = []
        self.fail = fail

    async def prepare_game_view(self, game, teams, orgs, dao) -> None:
        self.calls.append((game, list(teams), list(orgs), dao))
        if self.fail:
            raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_log_writer_writes_to_both() -> None:
    bot = RecordingLogWriter()
    web = RecordingLogWriter()
    writer = ComplexGameLogWriter(bot, web)
    event = GameLogEvent(type=GameLogType.GAME_STARTED)

    await writer.log(event)

    assert bot.calls == [event]
    assert web.calls == [event]


@pytest.mark.asyncio
async def test_log_writer_web_runs_even_if_bot_fails() -> None:
    bot = RecordingLogWriter(fail=True)
    web = RecordingLogWriter()
    writer = ComplexGameLogWriter(bot, web)
    event = GameLogEvent(type=GameLogType.GAME_FINISHED)

    await writer.log(event)

    assert bot.calls == [event]
    assert web.calls == [event]


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
