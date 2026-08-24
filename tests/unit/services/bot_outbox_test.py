import pytest
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)
from aiogram.methods import SendMessage

from shvatka.tgbot import tasks
from shvatka.tgbot.tasks import BotSenders, deliver_bot_views
from shvatka.tgbot.views.outbox import BotOutbox
from tests.mocks.nursery import FakeNursery


class RecordingSender:
    """Stands for a bot sender: writes down what it was asked to show.

    It answers to every name the outbox may call it by, so one class stands in
    for the view, the org notifier and the game log alike.
    """

    def __init__(self, journal: list[str], name: str, *, fail: bool = False) -> None:
        self.journal = journal
        self.name = name
        self.fail = fail

    async def game_finished_by_all(self, team) -> None:
        self._record(team)

    async def notify(self, event) -> None:
        self._record(event)

    async def log(self, log_event) -> None:
        self._record(log_event)

    def _record(self, what) -> None:
        self.journal.append(f"{self.name}: {what}")
        if self.fail:
            raise RuntimeError("boom")


class RecordingAlerter:
    def __init__(self, *, fail: bool = False) -> None:
        self.alerts: list[str] = []
        self.fail = fail

    async def alert(self, text: str) -> None:
        self.alerts.append(text)
        if self.fail:
            raise RuntimeError("alerting is broken too")


def build_senders(journal: list[str], *, failing: str | None = None) -> BotSenders:
    return BotSenders(
        view=RecordingSender(journal, "view", fail=failing == "view"),
        org_notifier=RecordingSender(journal, "org_notifier", fail=failing == "org_notifier"),
        game_log=RecordingSender(journal, "game_log", fail=failing == "game_log"),
    )


def test_flush_spawns_one_task_for_the_whole_recording() -> None:
    nursery = FakeNursery()
    outbox = BotOutbox(nursery=nursery)

    outbox.add(lambda senders: senders.view.game_finished_by_all("key is correct"))
    outbox.add(lambda senders: senders.view.game_finished_by_all("puzzle"))
    outbox.flush()

    assert len(nursery.spawned) == 1, "messages of one request must keep their order"
    task, kwargs = nursery.spawned[0]
    assert task is deliver_bot_views
    assert len(kwargs["calls"]) == 2


def test_nothing_recorded_nothing_spawned() -> None:
    nursery = FakeNursery()

    BotOutbox(nursery=nursery).flush()

    assert nursery.spawned == []


def test_flushing_twice_delivers_once() -> None:
    nursery = FakeNursery()
    outbox = BotOutbox(nursery=nursery)
    outbox.add(lambda senders: senders.view.game_finished_by_all("puzzle"))

    outbox.flush()
    outbox.flush()

    assert len(nursery.spawned) == 1


@pytest.mark.asyncio
async def test_delivered_in_the_order_they_were_recorded() -> None:
    journal: list[str] = []
    calls = [
        lambda senders: senders.view.game_finished_by_all("key is correct"),
        lambda senders: senders.view.game_finished_by_all("puzzle"),
        lambda senders: senders.org_notifier.notify("level up"),
    ]
    alerter = RecordingAlerter()
    senders = build_senders(journal)

    await deliver_bot_views(
        calls,
        view=senders.view,
        org_notifier=senders.org_notifier,
        game_log=senders.game_log,
        alerter=alerter,
    )

    assert journal == [
        "view: key is correct",
        "view: puzzle",
        "org_notifier: level up",
    ]
    assert alerter.alerts == []


@pytest.mark.asyncio
async def test_one_chat_failing_does_not_swallow_the_rest() -> None:
    journal: list[str] = []
    senders = build_senders(journal, failing="view")
    alerter = RecordingAlerter()

    await deliver_bot_views(
        [
            lambda s: s.view.game_finished_by_all("puzzle"),
            lambda s: s.org_notifier.notify("level up"),
        ],
        view=senders.view,
        org_notifier=senders.org_notifier,
        game_log=senders.game_log,
        alerter=alerter,
    )

    assert journal == ["view: puzzle", "org_notifier: level up"]
    # nobody is watching the response anymore, so a failure has to be shouted about
    assert len(alerter.alerts) == 1


@pytest.mark.asyncio
async def test_broken_alerting_does_not_break_delivery() -> None:
    journal: list[str] = []
    senders = build_senders(journal, failing="view")

    await deliver_bot_views(
        [
            lambda s: s.view.game_finished_by_all("puzzle"),
            lambda s: s.org_notifier.notify("level up"),
        ],
        view=senders.view,
        org_notifier=senders.org_notifier,
        game_log=senders.game_log,
        alerter=RecordingAlerter(fail=True),
    )

    assert journal == ["view: puzzle", "org_notifier: level up"]


class FlakySender:
    """Fails the first ``failures`` times it is called, then succeeds."""

    def __init__(self, journal: list[str], errors: list[Exception]) -> None:
        self.journal = journal
        self.errors = errors
        self.attempts = 0

    async def game_finished_by_all(self, team) -> None:
        self.attempts += 1
        if self.errors:
            error = self.errors.pop(0)
            self.journal.append(f"failed: {type(error).__name__}")
            raise error
        self.journal.append(f"sent: {team}")


def telegram_error(kind: type[TelegramAPIError], **kwargs) -> TelegramAPIError:
    return kind(method=SendMessage(chat_id=1, text="x"), message="boom", **kwargs)


@pytest.fixture
def fast_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tasks, "RETRY_BACKOFF", 0.001)


@pytest.mark.asyncio
async def test_a_dropped_connection_is_tried_again(fast_retries: None) -> None:
    journal: list[str] = []
    view = FlakySender(journal, [telegram_error(TelegramNetworkError)])
    alerter = RecordingAlerter()

    await deliver_bot_views(
        [lambda s: s.view.game_finished_by_all("puzzle")],
        view=view,
        org_notifier=RecordingSender(journal, "org_notifier"),
        game_log=RecordingSender(journal, "game_log"),
        alerter=alerter,
    )

    assert journal == ["failed: TelegramNetworkError", "sent: puzzle"]
    assert alerter.alerts == [], "a failure the retry fixed is not worth waking anyone for"


@pytest.mark.asyncio
async def test_giving_up_after_the_last_attempt(fast_retries: None) -> None:
    journal: list[str] = []
    view = FlakySender(journal, [telegram_error(TelegramServerError) for _ in range(5)])
    alerter = RecordingAlerter()

    await deliver_bot_views(
        [lambda s: s.view.game_finished_by_all("puzzle")],
        view=view,
        org_notifier=RecordingSender(journal, "org_notifier"),
        game_log=RecordingSender(journal, "game_log"),
        alerter=alerter,
    )

    assert view.attempts == tasks.DELIVERY_ATTEMPTS
    assert len(alerter.alerts) == 1


@pytest.mark.asyncio
async def test_being_kicked_from_a_chat_is_not_retried(fast_retries: None) -> None:
    journal: list[str] = []
    view = FlakySender(journal, [telegram_error(TelegramForbiddenError) for _ in range(5)])
    alerter = RecordingAlerter()

    await deliver_bot_views(
        [lambda s: s.view.game_finished_by_all("puzzle")],
        view=view,
        org_notifier=RecordingSender(journal, "org_notifier"),
        game_log=RecordingSender(journal, "game_log"),
        alerter=alerter,
    )

    assert view.attempts == 1, "the bot will be just as blocked in a second"
    assert len(alerter.alerts) == 1


@pytest.mark.asyncio
async def test_the_rest_of_the_recording_survives_a_retried_failure(fast_retries: None) -> None:
    journal: list[str] = []
    view = FlakySender(journal, [telegram_error(TelegramServerError) for _ in range(5)])
    org_notifier = RecordingSender(journal, "org_notifier")

    await deliver_bot_views(
        [
            lambda s: s.view.game_finished_by_all("puzzle"),
            lambda s: s.org_notifier.notify("level up"),
        ],
        view=view,
        org_notifier=org_notifier,
        game_log=RecordingSender(journal, "game_log"),
        alerter=RecordingAlerter(),
    )

    assert journal[-1] == "org_notifier: level up"


def test_flood_control_waits_exactly_as_long_as_telegram_asked() -> None:
    error = telegram_error(TelegramRetryAfter, retry_after=7)

    assert tasks._retry_delay(error, attempt=1) == 7


def test_a_flood_wait_longer_than_the_game_can_afford_is_not_waited_out() -> None:
    error = telegram_error(TelegramRetryAfter, retry_after=int(tasks.MAX_RETRY_DELAY) + 1)

    assert tasks._retry_delay(error, attempt=1) is None


def test_backoff_grows_between_attempts() -> None:
    error = telegram_error(TelegramNetworkError)
    delays = [tasks._retry_delay(error, attempt=i) for i in (1, 2, 3)]

    assert delays == [tasks.RETRY_BACKOFF, tasks.RETRY_BACKOFF * 2, tasks.RETRY_BACKOFF * 4]
