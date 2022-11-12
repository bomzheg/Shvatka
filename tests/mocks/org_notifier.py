from shvatka.views.game import OrgNotifier, Event


class OrgNotifierMock(OrgNotifier):
    async def notify(self, event: Event) -> None:
        pass
