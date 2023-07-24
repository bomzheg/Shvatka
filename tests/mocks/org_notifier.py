from shvatka.core.views.game import OrgNotifier, Event


class OrgNotifierMock(OrgNotifier):
    def __init__(self) -> None:
        self.calls: list[Event] = []

    def assert_one_event(self, event: Event) -> None:
        assert len(self.calls) == 1
        assert event == self.calls.pop()

    def assert_no_calls(self):
        assert len(self.calls) == 0

    async def notify(self, event: Event) -> None:
        self.calls.append(event)
