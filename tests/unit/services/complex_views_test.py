import pytest

from shvatka.core.models import dto
from shvatka.core.models.dto import action
from shvatka.core.views.game import (
    GameLogWriter,
    GameLogEvent,
    GameLogType,
    GameView,
    GameViewPreparer,
    InputContainer,
)
from shvatka.tgbot.views.outbox import BotOutbox
from shvatka.views import ComplexGameLogWriter, ComplexGameViewPreparer, ComplexView
from tests.mocks.nursery import FakeNursery, deliver_recorded


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


class RecordingGameView(GameView):
    """A view that only writes down what it was asked to show, in order."""

    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[str] = []
        self.fail = fail

    async def send_puzzle(self, team: dto.Team, level: dto.Level) -> None:
        self._record("send_puzzle")

    async def send_hint(self, team: dto.Team, hint_number: int, level: dto.Level) -> None:
        self._record("send_hint")

    async def duplicate_key(self, key: dto.KeyTime, input_container: InputContainer) -> None:
        self._record("duplicate_key")

    async def wrong_key(self, key: dto.KeyTime, input_container: InputContainer) -> None:
        self._record("wrong_key")

    async def effects_key(
        self, key: dto.KeyTime, effects: action.Effects, input_container: InputContainer
    ) -> None:
        self._record("effects_key")

    async def game_finished(self, team: dto.Team, input_container: InputContainer) -> None:
        self._record("game_finished")

    async def game_finished_by_all(self, team: dto.Team) -> None:
        self._record("game_finished_by_all")

    async def effects(
        self, team: dto.Team, effects: action.Effects, input_container: InputContainer
    ) -> None:
        self._record("effects")

    def _record(self, name: str) -> None:
        self.calls.append(name)
        if self.fail:
            raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_key_answered_before_telegram_is_written_to() -> None:
    bot = RecordingGameView()
    web = RecordingGameView()
    outbox = BotOutbox(nursery=FakeNursery())
    view = ComplexView(outbox, web)

    await view.effects_key(key=None, effects=None, input_container=None)
    await view.send_puzzle(team=None, level=None)

    assert web.calls == ["effects_key", "send_puzzle"], "the response is built now"
    assert bot.calls == [], "a puzzle is minutes of messages — not the caller's wait"

    await deliver_recorded(outbox, view=bot)

    assert bot.calls == ["effects_key", "send_puzzle"], "a key is confirmed before its puzzle"


@pytest.mark.asyncio
async def test_bot_still_shown_even_if_web_fails() -> None:
    bot = RecordingGameView()
    web = RecordingGameView(fail=True)
    outbox = BotOutbox(nursery=FakeNursery())
    view = ComplexView(outbox, web)

    await view.wrong_key(key=None, input_container=None)
    await deliver_recorded(outbox, view=bot)

    assert web.calls == ["wrong_key"]
    assert bot.calls == ["wrong_key"]


@pytest.mark.asyncio
async def test_log_writer_writes_web_now_and_bot_after() -> None:
    bot = RecordingLogWriter()
    web = RecordingLogWriter()
    outbox = BotOutbox(nursery=FakeNursery())
    writer = ComplexGameLogWriter(outbox, web)
    event = GameLogEvent(type=GameLogType.GAME_STARTED)

    await writer.log(event)

    assert web.calls == [event]
    assert bot.calls == []

    await deliver_recorded(outbox, game_log=bot)

    assert bot.calls == [event]


@pytest.mark.asyncio
async def test_log_writer_writes_to_bot_even_if_web_fails() -> None:
    bot = RecordingLogWriter()
    web = RecordingLogWriter(fail=True)
    outbox = BotOutbox(nursery=FakeNursery())
    writer = ComplexGameLogWriter(outbox, web)
    event = GameLogEvent(type=GameLogType.GAME_FINISHED)

    await writer.log(event)
    await deliver_recorded(outbox, game_log=bot)

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
