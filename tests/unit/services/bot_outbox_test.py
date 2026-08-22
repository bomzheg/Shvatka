import pytest

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
