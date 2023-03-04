from src.shvatka.models import dto
from src.shvatka.views.level import LevelView


class LevelViewMock(LevelView):
    def __init__(self):
        self.calls = {}

    async def send_puzzle(self, suite: dto.LevelTestSuite) -> None:
        self.calls.setdefault("send_puzzle", []).append(suite)

    async def send_hint(self, suite: dto.LevelTestSuite, hint_number: int) -> None:
        self.calls.setdefault("send_hint", []).append((suite, hint_number))

    async def correct_key(self, suite: dto.LevelTestSuite, key: str) -> None:
        self.calls.setdefault("correct_key", []).append((suite, key))

    async def wrong_key(self, suite: dto.LevelTestSuite, key: str) -> None:
        self.calls.setdefault("wrong_key", []).append((suite, key))

    async def level_finished(self, suite: dto.LevelTestSuite) -> None:
        self.calls.setdefault("level_finished", []).append(suite)
