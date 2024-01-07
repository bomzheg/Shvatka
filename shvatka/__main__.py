import logging

import uvicorn
from fastapi import FastAPI

from shvatka.infrastructure.clients.factory import create_file_storage
from shvatka.tgbot.config.parser.main import load_config as load_bot_config
from shvatka.api.config.parser.main import load_config as load_api_config
from shvatka.api.main_factory import (
    get_paths,
    create_app,
)
from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.infrastructure.db.factory import create_redis, create_engine, create_session_maker
from shvatka.tgbot.main_factory import resolve_update_types, DpBuilder
from shvatka.tgbot.utils.fastapi_webhook import setup_application, SimpleRequestHandler

logger = logging.getLogger(__name__)


async def main() -> FastAPI:
    paths = get_paths()

    setup_logging(paths)
    api_config = load_api_config(paths)
    bot_config = load_bot_config(paths)
    webhook_config = bot_config.bot.webhook
    if not webhook_config:
        raise EnvironmentError("No webhook configuration provided")
    engine = create_engine(api_config.db)
    pool = create_session_maker(engine)
    file_storage = create_file_storage(api_config.file_storage_config)
    app = create_app(pool=pool, redis=create_redis(api_config.redis), config=api_config)
    bot, dp = await DpBuilder(bot_config, pool, file_storage).build()
    setup_application(app, dp)
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        handle_in_background=False,
        secret_token=webhook_config.path,
    )
    webhook_handler.register(app, webhook_config.path)
    await bot.set_webhook(
        url=webhook_config.web_url + webhook_config.path,
        secret_token=webhook_config.secret,
        allowed_updates=resolve_update_types(dp),
    )
    logger.info("app prepared")
    return app


def run():
    uvicorn.run("shvatka.api:main", factory=True, log_config=None)


if __name__ == "__main__":
    run()
