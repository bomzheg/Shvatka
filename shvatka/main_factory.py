import logging
import time
from functools import partial

from aiogram import Bot, Dispatcher
from dishka import (
    Provider,
    Scope,
    AsyncContainer,
    provide,
    make_async_container,
    plotter,
    STRICT_VALIDATION,
)
from dishka.exceptions import NoContextValueError
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from shvatka.api.app.dependencies import get_api_specific_providers
from shvatka.api.app.dependencies.auth import ApiIdentityProvider
from shvatka.api.app.config.parser.main import load_config as load_api_config
from shvatka.api.app.utils.web_input import (
    WebGameView,
    WebTeamNotifier,
    WebOrgNotifier,
    WebGamePreparer,
    WebGameLogWriter,
)
from shvatka.api.main_factory import create_app
from shvatka.common.config.models.paths import Paths
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.views.game import (
    GameView,
    GameViewPreparer,
    OrgNotifier,
    GameLogWriter,
)
from shvatka.core.views.team import TeamNotifier
from shvatka.infrastructure.di import get_providers
from shvatka.infrastructure.di.utils import warm_up
from shvatka.tgbot.config.models.bot import WebhookConfig
from shvatka.tgbot.config.parser.main import load_config as load_bot_config
from shvatka.tgbot.main_factory import (
    resolve_update_types,
    get_bot_specific_providers,
)
from shvatka.tgbot.services.identity import TgBotIdentityProvider
from shvatka.tgbot.utils.fastapi_webhook import setup_application, SimpleRequestHandler
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
    def complex_team_notifier(self, bot: BotTeamNotifier, web: WebTeamNotifier) -> TeamNotifier:
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


def get_root_app_providers(paths_env: str) -> list[Provider]:
    return [
        *get_providers(paths_env),
        *get_bot_specific_providers(),
        *get_api_specific_providers(),
        *get_complex_only_providers(),
    ]


def create_root_app(paths: Paths) -> FastAPI:
    started_at = time.monotonic()
    api_config = load_api_config(paths)
    bot_config = load_bot_config(paths)
    webhook_config = bot_config.bot.webhook
    if not webhook_config:
        raise EnvironmentError("No webhook configuration provided")

    app = create_app(api_config)
    dishka = make_async_container(
        *get_root_app_providers("SHVATKA_PATH"),
        validation_settings=STRICT_VALIDATION,
    )
    setup_application(app, dishka)
    webhook_handler = SimpleRequestHandler(
        handle_in_background=False,
        secret_token=webhook_config.secret,
    )
    webhook_handler.register(app, webhook_config.path)

    root_app = FastAPI()
    root_app.mount(api_config.api.context_path, app)
    setup = partial(on_startup, dishka, webhook_config)
    root_app.router.add_event_handler("startup", setup)
    setup_dishka(dishka, root_app)
    # dishka's fastapi integration doesn't close the container itself, and
    # app-scoped things (the nursery among them) finalize on that close
    root_app.router.add_event_handler("shutdown", dishka.close)
    logger.info(
        "app prepared in %.2f s with dishka:\n%s",
        time.monotonic() - started_at,
        plotter.render_d2(dishka),
    )
    return root_app


async def on_startup(dishka: AsyncContainer, webhook_config: WebhookConfig):
    webhook_url = webhook_config.web_url + webhook_config.path
    logger.info("as webhook url used %s", webhook_url)
    bot = await dishka.get(Bot)
    dp = await dishka.get(Dispatcher)
    await bot.set_webhook(
        url=webhook_url,
        secret_token=webhook_config.secret,
        allowed_updates=resolve_update_types(dp),
    )
    await warm_up(dishka)
