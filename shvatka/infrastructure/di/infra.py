from dishka import Provider, provide, Scope

from shvatka.api.dependencies.api_only import MockUsedOneTimeTokenInteractor
from shvatka.core.models import dto
from shvatka.core.models.dto import action
from shvatka.core.views.game import (
    GameView,
    InputContainer,
    GameLogWriter,
    GameLogEvent,
    OrgNotifier,
    Event,
)
from shvatka.core.views.team import TeamNotifier, TeamEvent
from shvatka.infrastructure.bus.in_memory import UsedOneTimeTokenInteractor


class NoOpGameView(GameView):
    async def send_puzzle(self, team: dto.Team, level: dto.Level) -> None:
        pass

    async def send_hint(self, team: dto.Team, hint_number: int, level: dto.Level) -> None:
        pass

    async def duplicate_key(self, key: dto.KeyTime, input_container: InputContainer) -> None:
        pass

    async def wrong_key(self, key: dto.KeyTime, input_container: InputContainer) -> None:
        pass

    async def effects_key(
        self, key: dto.KeyTime, effects: action.Effects, input_container: InputContainer
    ) -> None:
        pass

    async def game_finished(self, team: dto.Team, input_container: InputContainer) -> None:
        pass

    async def game_finished_by_all(self, team: dto.Team) -> None:
        pass

    async def effects(
        self, team: dto.Team, effects: action.Effects, input_container: InputContainer
    ) -> None:
        pass


class NoOpGameLogWriter(GameLogWriter):
    async def log(self, log_event: GameLogEvent) -> None:
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
    def org_notifier(self) -> OrgNotifier:
        return NoOpOrgNotifier()

    @provide
    def team_notifier(self) -> TeamNotifier:
        return NoOpTeamNotifier()


def get_infra_only_providers() -> list[Provider]:
    return [InfrastructureProvider()]
