from dishka import Provider, Scope, provide

from shvatka.api.utils.web_input import WebInput, WebGameView, WebGameLogWriter, WebOrgNotifier


class OtherApiProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def input(self) -> WebInput:
        return WebInput()

    @provide
    def view(self) -> WebGameView:
        return WebGameView()

    @provide
    def log_writer(self) -> WebGameLogWriter:
        return WebGameLogWriter()

    @provide
    def org_notifier(self) -> WebOrgNotifier:
        return WebOrgNotifier()
