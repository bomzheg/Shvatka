"""Showing something when nobody is waiting for it, and when it goes wrong."""

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
from shvatka.tgbot.tasks import deliver


class FlakySender:
    """Fails with the given errors, in order, then succeeds."""

    def __init__(self, journal: list[str], errors: list[Exception] | None = None) -> None:
        self.journal = journal
        self.errors = errors or []
        self.attempts = 0

    async def show(self, what: str) -> None:
        self.attempts += 1
        if self.errors:
            error = self.errors.pop(0)
            self.journal.append(f"failed: {type(error).__name__}")
            raise error
        self.journal.append(f"sent: {what}")


class RecordingAlerter:
    def __init__(self, *, fail: bool = False) -> None:
        self.alerts: list[str] = []
        self.fail = fail

    async def alert(self, text: str) -> None:
        self.alerts.append(text)
        if self.fail:
            raise RuntimeError("alerting is broken too")


def telegram_error(kind: type[TelegramAPIError], **kwargs) -> TelegramAPIError:
    return kind(method=SendMessage(chat_id=1, text="x"), message="boom", **kwargs)


@pytest.fixture
def fast_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tasks, "RETRY_BACKOFF", 0.001)


@pytest.mark.asyncio
async def test_what_worked_is_not_alerted_about() -> None:
    journal: list[str] = []
    sender = FlakySender(journal)
    alerter = RecordingAlerter()

    await deliver(lambda: sender.show("puzzle"), alerter)

    assert journal == ["sent: puzzle"]
    assert alerter.alerts == []


@pytest.mark.asyncio
async def test_a_dropped_connection_is_tried_again(fast_retries: None) -> None:
    journal: list[str] = []
    sender = FlakySender(journal, [telegram_error(TelegramNetworkError)])
    alerter = RecordingAlerter()

    await deliver(lambda: sender.show("puzzle"), alerter)

    assert journal == ["failed: TelegramNetworkError", "sent: puzzle"]
    assert alerter.alerts == [], "a failure the retry fixed is not worth waking anyone for"


@pytest.mark.asyncio
async def test_giving_up_after_the_last_attempt(fast_retries: None) -> None:
    journal: list[str] = []
    sender = FlakySender(journal, [telegram_error(TelegramServerError) for _ in range(5)])
    alerter = RecordingAlerter()

    await deliver(lambda: sender.show("puzzle"), alerter)

    assert sender.attempts == tasks.DELIVERY_ATTEMPTS
    assert len(alerter.alerts) == 1, "nobody is watching the response, so it has to be shouted"


@pytest.mark.asyncio
async def test_being_kicked_from_a_chat_is_not_retried(fast_retries: None) -> None:
    journal: list[str] = []
    sender = FlakySender(journal, [telegram_error(TelegramForbiddenError) for _ in range(5)])
    alerter = RecordingAlerter()

    await deliver(lambda: sender.show("puzzle"), alerter)

    assert sender.attempts == 1, "the bot will be just as blocked in a second"
    assert len(alerter.alerts) == 1


@pytest.mark.asyncio
async def test_a_failure_is_contained_not_raised(fast_retries: None) -> None:
    journal: list[str] = []
    sender = FlakySender(journal, [telegram_error(TelegramForbiddenError)])

    await deliver(lambda: sender.show("puzzle"), RecordingAlerter())

    # the caller keeps going: one chat that can't be written to must not cost
    # the rest of the batch its messages
    await deliver(lambda: FlakySender(journal).show("next"), RecordingAlerter())
    assert journal[-1] == "sent: next"


@pytest.mark.asyncio
async def test_broken_alerting_does_not_break_delivery(fast_retries: None) -> None:
    journal: list[str] = []
    sender = FlakySender(journal, [telegram_error(TelegramForbiddenError)])

    await deliver(lambda: sender.show("puzzle"), RecordingAlerter(fail=True))

    assert journal == ["failed: TelegramForbiddenError"]


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
