from shvatka.core.views.game import GameLogWriter, GameLogEvent


class GameLogWriterMock(GameLogWriter):
    def __init__(self) -> None:
        self.requests: list[GameLogEvent] = []

    def assert_one_event(self, event: GameLogEvent):
        assert len(self.requests) == 1
        assert self.requests.pop() == event

    async def log(self, log_event: GameLogEvent) -> None:
        self.requests.append(log_event)
