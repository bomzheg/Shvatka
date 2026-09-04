from shvatka.core.models import dto
from shvatka.core.views.game import GameReleasePublisher


class GameReleasePublisherMock(GameReleasePublisher):
    def __init__(self) -> None:
        self.published: list[dto.GameRelease] = []
        self.updated: list[dto.GameRelease] = []
        self.unpublished: list[int] = []

    async def publish(self, game: dto.Game, release: dto.GameRelease) -> None:
        self.published.append(release)

    async def update(self, game: dto.Game, release: dto.GameRelease) -> None:
        self.updated.append(release)

    async def unpublish(self, game: dto.Game) -> None:
        self.unpublished.append(game.id)
