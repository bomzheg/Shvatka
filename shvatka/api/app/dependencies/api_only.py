from dishka import Provider, Scope, provide

from shvatka.api.app.dependencies.auth import ApiIdentityProvider
from shvatka.api.app.utils.web_input import (
    WebGameLogWriter,
    WebGamePreparer,
    WebGameReleasePublisher,
    WebGameView,
    WebOrgNotifier,
    WebTeamNotifier,
)
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.nursery import Nursery
from shvatka.core.views.game import (
    GameLogWriter,
    GameReleasePublisher,
    GameView,
    GameViewPreparer,
    OrgNotifier,
    ViewSender,
)
from shvatka.core.views.team import TeamNotifier
from shvatka.infrastructure.bus.in_memory import UsedOneTimeTokenInteractor
from shvatka.tgbot.tasks import NurseryViewSender


class MockUsedOneTimeTokenInteractor(UsedOneTimeTokenInteractor):
    async def __call__(self, player_id: int) -> None:
        pass


class ApiOnlyProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_idp(self, idp: ApiIdentityProvider) -> IdentityProvider:
        return idp

    @provide
    def view_sender(self, nursery: Nursery) -> ViewSender:
        return NurseryViewSender(nursery)

    @provide
    def web_only_view(self, view: WebGameView) -> GameView:
        return view

    @provide
    def web_only_log_writer(self, log_writer: WebGameLogWriter) -> GameLogWriter:
        return log_writer

    @provide
    def web_only_release_publisher(
        self, publisher: WebGameReleasePublisher
    ) -> GameReleasePublisher:
        return publisher

    @provide
    def web_only_org_notifier(self, org_notifier: WebOrgNotifier) -> OrgNotifier:
        return org_notifier

    @provide
    def web_only_team_notifier(self, team_notifier: WebTeamNotifier) -> TeamNotifier:
        return team_notifier

    @provide
    def web_only_preparer_view(self, preparer: WebGamePreparer) -> GameViewPreparer:
        return preparer

    @provide
    def used_one_time_token_interactor(self) -> UsedOneTimeTokenInteractor:
        return MockUsedOneTimeTokenInteractor()
