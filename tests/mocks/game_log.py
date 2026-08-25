from typing import Sequence

from shvatka.core.views.game import GameLogWriter, GameLogEvent


class GameLogWriterMock(GameLogWriter):
    def __init__(self) -> None:
        self.requests: list[GameLogEvent] = []

    def assert_one_event(self, event: GameLogEvent) -> None:
        assert len(self.requests) == 1
        assert self.requests.pop() == event

    async def log(self, log_events: Sequence[GameLogEvent]) -> None:
        self.requests.extend(log_events)
