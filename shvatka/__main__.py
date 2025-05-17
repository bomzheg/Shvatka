import logging
from functools import partial

import uvicorn
from aiogram import Bot, Dispatcher
from dishka import AsyncContainer, make_async_container, plotter, STRICT_VALIDATION
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from shvatka.api.dependencies import get_api_specific_providers
from shvatka.infrastructure.di import get_providers
from shvatka.infrastructure.di.utils import warm_up
from shvatka.main_factory import get_complex_only_providers
from shvatka.tgbot.config.models.bot import WebhookConfig
from shvatka.tgbot.config.parser.main import load_config as load_bot_config
from shvatka.api.config.parser.main import load_config as load_api_config
from shvatka.api.main_factory import (
    get_paths,
    create_app,
)
from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.tgbot.main_factory import (
    resolve_update_types,
    get_bot_specific_providers,
)
from shvatka.tgbot.utils.fastapi_webhook import setup_application, SimpleRequestHandler

logger = logging.getLogger(__name__)


def main() -> FastAPI:
    paths = get_paths()

    setup_logging(paths)
    api_config = load_api_config(paths)
    bot_config = load_bot_config(paths)
    webhook_config = bot_config.bot.webhook
    if not webhook_config:
        raise EnvironmentError("No webhook configuration provided")

    app = create_app(api_config)
    dishka = make_async_container(
        *get_providers("SHVATKA_PATH"),
        *get_bot_specific_providers(),
        *get_api_specific_providers(),
        *get_complex_only_providers(),
        validation_settings=STRICT_VALIDATION,
    )
    setup_application(app, dishka)
    webhook_handler = SimpleRequestHandler(
        handle_in_background=False,
        secret_token=webhook_config.secret,
    )
    webhook_handler.register(app, webhook_config.path)

    root_app = FastAPI()
    root_app.mount(api_config.context_path, app)
    setup = partial(on_startup, dishka, webhook_config)
    root_app.router.add_event_handler("startup", setup)
    setup_dishka(dishka, root_app)
    logger.info(
        "app prepared with dishka:\n%s",
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


def run():
    uvicorn.run(
        "shvatka.__main__:main",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        factory=True,
        log_config=None,
    )


if __name__ == "__main__":
    run()
