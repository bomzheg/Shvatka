import pytest

from shvatka.core.views.game import Event, OrgNotifier
from shvatka.tgbot.views.outbox import BotOutbox
from shvatka.views import ComplexOrgNotifier
from tests.mocks.nursery import FakeNursery, deliver_recorded


class RecordingNotifier(OrgNotifier):
    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[Event] = []
        self.fail = fail

    async def notify(self, event: Event) -> None:
        self.calls.append(event)
        if self.fail:
            raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_web_notified_now_bot_notified_after() -> None:
    bot = RecordingNotifier()
    web = RecordingNotifier()
    outbox = BotOutbox(nursery=FakeNursery())
    notifier = ComplexOrgNotifier(outbox, web)
    event = Event(orgs_list=[])

    await notifier.notify(event)

    assert web.calls == [event]
    assert bot.calls == [], "telegram is not written to while the caller waits"

    await deliver_recorded(outbox, org_notifier=bot)

    assert bot.calls == [event]


@pytest.mark.asyncio
async def test_bot_notified_even_if_web_fails() -> None:
    bot = RecordingNotifier()
    web = RecordingNotifier(fail=True)
    outbox = BotOutbox(nursery=FakeNursery())
    notifier = ComplexOrgNotifier(outbox, web)
    event = Event(orgs_list=[])

    await notifier.notify(event)
    await deliver_recorded(outbox, org_notifier=bot)

    assert bot.calls == [event]
    assert web.calls == [event]
