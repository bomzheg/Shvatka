from src.core.views.game import OrgNotifier, Event


class OrgNotifierMock(OrgNotifier):
    def __init__(self):
        self.calls: list[Event] = []

    async def notify(self, event: Event) -> None:
        self.calls.append(event)
