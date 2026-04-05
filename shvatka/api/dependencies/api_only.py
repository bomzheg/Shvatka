from dishka import Provider, Scope, provide

from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.utils.web_input import WebGameView, WebGameLogWriter, WebOrgNotifier, WebGamePreparer
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.views.game import GameView, GameLogWriter, OrgNotifier, GameViewPreparer


class ApiOnlyProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_idp(self, idp: ApiIdentityProvider) -> IdentityProvider:
        return idp

    @provide
    def web_only_view(self, view: WebGameView) -> GameView:
        return view

    @provide
    def web_only_log_writer(self, log_writer: WebGameLogWriter) -> GameLogWriter:
        return log_writer

    @provide
    def web_only_org_notifier(self, org_notifier: WebOrgNotifier) -> OrgNotifier:
        return org_notifier

    @provide
    def web_only_preparer_view(self) -> GameViewPreparer:
        return WebGamePreparer()
