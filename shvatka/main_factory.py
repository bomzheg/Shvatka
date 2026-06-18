import logging

from dishka import Provider, Scope, AsyncContainer, provide
from dishka.exceptions import NoContextValueError

from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.utils.web_input import (
    WebGameView,
    WebTeamNotifier,
    WebOrgNotifier,
    WebGamePreparer,
    WebGameLogWriter,
)
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.views.game import (
    GameView,
    GameViewPreparer,
    OrgNotifier,
    GameLogWriter,
)
from shvatka.core.views.team import TeamNotifier
from shvatka.tgbot.services.identity import TgBotIdentityProvider
from shvatka.tgbot.views.game import BotView, BotOrgNotifier, GameBotLog
from shvatka.tgbot.views.team import BotTeamNotifier
from shvatka.views import (
    ComplexOrgNotifier,
    ComplexGameViewPreparer,
    ComplexGameLogWriter,
    ComplexTeamNotifier,
    ComplexView,
)

logger = logging.getLogger(__name__)


class ComplexOnlyProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def get_idp(self, container: AsyncContainer) -> IdentityProvider:
        try:
            return await container.get(TgBotIdentityProvider)
        except NoContextValueError:
            return await container.get(ApiIdentityProvider)

    @provide
    def complex_view(self, bot_view: BotView, web_view: WebGameView) -> GameView:
        return ComplexView(bot_view, web_view)

    @provide
    def complex_preparer(
        self, bot_view: BotView, web_preparer: WebGamePreparer
    ) -> GameViewPreparer:
        return ComplexGameViewPreparer(bot_view, web_preparer)

    @provide
    def complex_team_notifier(
        self, bot: BotTeamNotifier, web: WebTeamNotifier
    ) -> TeamNotifier:
        return ComplexTeamNotifier(bot, web)

    @provide
    def complex_org_notifier(self, bot: BotOrgNotifier, web: WebOrgNotifier) -> OrgNotifier:
        return ComplexOrgNotifier(bot, web)

    @provide
    def complex_log_writer(self, bot: GameBotLog, web: WebGameLogWriter) -> GameLogWriter:
        return ComplexGameLogWriter(bot, web)


def get_complex_only_providers() -> list[Provider]:
    return [
        ComplexOnlyProvider(),
    ]
