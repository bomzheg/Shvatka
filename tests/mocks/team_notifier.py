from shvatka.core.views.team import TeamEvent, TeamNotifier


class TeamNotifierMock(TeamNotifier):
    def __init__(self) -> None:
        self.events: list[TeamEvent] = []

    async def notify(self, event: TeamEvent) -> None:
        self.events.append(event)
