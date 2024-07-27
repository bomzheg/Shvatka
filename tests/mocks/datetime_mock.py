from collections import deque
from datetime import tzinfo, datetime


class ClockMock:
    def __init__(self) -> None:
        self.mocks: deque[tuple[tzinfo, datetime]] = deque([])
        self.calls: list[tuple[tzinfo, datetime]] = []

    def __call__(self, tz: tzinfo | None = None) -> datetime:
        try:
            tz_get, result = self.mocks.popleft()
            assert tz_get == tz
        except IndexError:
            result = datetime.now(tz=tz)
        self.calls.append((tz, result))
        return result

    def add_mock(self, tz: tzinfo | None, result: datetime) -> None:
        self.mocks.append((tz, result))
