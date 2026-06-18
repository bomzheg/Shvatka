import pytest

from shvatka.core.views.game import Event, OrgNotifier
from shvatka.main_factory import ComplexOrgNotifier


class RecordingNotifier(OrgNotifier):
    def __init__(self, *, fail: bool = False) -> None:
        self.calls: list[Event] = []
        self.fail = fail

    async def notify(self, event: Event) -> None:
        self.calls.append(event)
        if self.fail:
            raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_notifies_both_bot_and_web() -> None:
    bot = RecordingNotifier()
    web = RecordingNotifier()
    notifier = ComplexOrgNotifier(bot, web)
    event = Event(orgs_list=[])

    await notifier.notify(event)

    assert bot.calls == [event]
    assert web.calls == [event]


@pytest.mark.asyncio
async def test_web_notified_even_if_bot_fails() -> None:
    bot = RecordingNotifier(fail=True)
    web = RecordingNotifier()
    notifier = ComplexOrgNotifier(bot, web)
    event = Event(orgs_list=[])

    await notifier.notify(event)

    assert bot.calls == [event]
    assert web.calls == [event]


@pytest.mark.asyncio
async def test_bot_notified_even_if_web_fails() -> None:
    bot = RecordingNotifier()
    web = RecordingNotifier(fail=True)
    notifier = ComplexOrgNotifier(bot, web)
    event = Event(orgs_list=[])

    await notifier.notify(event)

    assert bot.calls == [event]
    assert web.calls == [event]
