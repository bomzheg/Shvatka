from shvatka.core.views.game import GameLogWriter, GameLogEvent


class GameLogWriterMock(GameLogWriter):
    def __init__(self) -> None:
        self.requests: list[GameLogEvent] = []

    async def log(self, log_event: GameLogEvent) -> None:
        self.requests.append(log_event)
