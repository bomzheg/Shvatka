from shvatka.core.models import dto
from shvatka.core.views.game import GameReleasePublisher


class GameReleasePublisherMock(GameReleasePublisher):
    def __init__(self) -> None:
        self.published: list[dto.GameRelease] = []

    async def publish(self, game: dto.Game, release: dto.GameRelease) -> None:
        self.published.append(release)
