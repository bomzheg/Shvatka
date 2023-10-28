import asyncio
import logging

from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.infrastructure.clients.factory import create_file_storage
from shvatka.infrastructure.db.factory import (
    create_session_maker,
    create_engine,
)
from shvatka.tgbot.config.parser.main import load_config
from shvatka.tgbot.main_factory import (
    get_paths,
    prepare_dp_full,
)
from shvatka.tgbot.utils.router import print_router_tree

logger = logging.getLogger(__name__)


async def main():
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    engine = create_engine(config.db)
    pool = create_session_maker(engine)
    file_storage = create_file_storage(config.file_storage_config)

    async with prepare_dp_full(config, pool, file_storage) as (bot, dp):
        logger.info("started with configured routers \n%s", print_router_tree(dp))
        try:
            await dp.start_polling(
                bot, allowed_updates=dp.resolve_used_update_types(skip_events={"aiogd_update"})
            )
        finally:
            await engine.dispose()
            logger.info("stopped")


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
