from typing import Sequence

from dishka import Provider, provide, Scope

from shvatka.api.app.dependencies.api_only import MockUsedOneTimeTokenInteractor
from shvatka.core.models import dto
from shvatka.core.views.game import (
    AnyViewTask,
    GameView,
    GameLogWriter,
    GameLogEvent,
    GameReleasePublisher,
    OrgNotifier,
    Event,
)
from shvatka.core.views.team import TeamNotifier, TeamEvent
from shvatka.infrastructure.bus.in_memory import UsedOneTimeTokenInteractor


class NoOpGameView(GameView):
    async def show(self, tasks: Sequence[AnyViewTask]) -> None:
        pass


class NoOpGameLogWriter(GameLogWriter):
    async def log(self, log_event: GameLogEvent) -> None:
        pass


class NoOpGameReleasePublisher(GameReleasePublisher):
    async def publish(self, game: dto.Game, release: dto.GameRelease) -> None:
        pass

    async def update(self, game: dto.Game, release: dto.GameRelease) -> None:
        pass

    async def unpublish(self, game: dto.Game) -> None:
        pass


class NoOpOrgNotifier(OrgNotifier):
    async def notify(self, event: Event) -> None:
        pass


class NoOpTeamNotifier(TeamNotifier):
    async def notify(self, event: TeamEvent) -> None:
        pass


class InfrastructureProvider(Provider):
    scope = Scope.APP

    @provide
    def ott_provider(self) -> UsedOneTimeTokenInteractor:
        return MockUsedOneTimeTokenInteractor()

    @provide
    def game_view(self) -> GameView:
        return NoOpGameView()

    @provide
    def log_writer(self) -> GameLogWriter:
        return NoOpGameLogWriter()

    @provide
    def release_publisher(self) -> GameReleasePublisher:
        return NoOpGameReleasePublisher()

    @provide
    def org_notifier(self) -> OrgNotifier:
        return NoOpOrgNotifier()

    @provide
    def team_notifier(self) -> TeamNotifier:
        return NoOpTeamNotifier()


def get_infra_only_providers() -> list[Provider]:
    return [InfrastructureProvider()]
