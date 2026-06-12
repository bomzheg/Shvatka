from dishka import Provider, Scope, provide

from shvatka.api.config.models.main import ApiConfig
from shvatka.api.utils.push import WebPushSender
from shvatka.api.utils.web_input import WebInput, WebGameView, WebGameLogWriter, WebOrgNotifier
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.infrastructure.db.dao.rdb.push_subscription import PushSubscriptionDAO


class OtherApiProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def input(self) -> WebInput:
        return WebInput()

    @provide
    def push_sender(self, config: ApiConfig, dao: PushSubscriptionDAO) -> WebPushSender:
        return WebPushSender(config=config.push, dao=dao)

    @provide
    def view(self, push_sender: WebPushSender, current_game: CurrentGameProvider) -> WebGameView:
        return WebGameView(push_sender, current_game)

    @provide
    def log_writer(self) -> WebGameLogWriter:
        return WebGameLogWriter()

    @provide
    def org_notifier(self) -> WebOrgNotifier:
        return WebOrgNotifier()
