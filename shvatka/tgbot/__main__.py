import asyncio
import logging

from aiogram_dialog.manager.message_manager import MessageManager

from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.common.factory import create_telegraph, create_dataclass_factory
from shvatka.infrastructure.clients.factory import create_file_storage
from shvatka.infrastructure.db.factory import (
    create_lock_factory,
    create_level_test_dao,
    create_session_maker,
    create_engine,
)
from shvatka.infrastructure.scheduler.factory import create_scheduler
from shvatka.tgbot.config.parser.main import load_config
from shvatka.tgbot.main_factory import (
    create_bot,
    create_dispatcher,
    get_paths,
    create_redis,
)
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.utils.router import print_router_tree
from shvatka.tgbot.views.jinja_filters import setup_jinja

logger = logging.getLogger(__name__)


async def main():
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    dcf = create_dataclass_factory()
    file_storage = create_file_storage(config.file_storage_config)
    engine = create_engine(config.db)
    pool = create_session_maker(engine)
    bot = create_bot(config)
    setup_jinja(bot=bot)
    level_test_dao = create_level_test_dao()

    async with (
        UserGetter(config.tg_client) as user_getter,
        create_redis(config.redis) as redis,
        create_scheduler(
            pool=pool,
            redis=redis,
            bot=bot,
            redis_config=config.redis,
            game_log_chat=config.bot.log_chat,
            file_storage=file_storage,
            level_test_dao=level_test_dao,
        ) as scheduler,
        bot.context(),
    ):
        dp = create_dispatcher(
            config=config,
            user_getter=user_getter,
            dcf=dcf,
            pool=pool,
            redis=redis,
            scheduler=scheduler,
            locker=create_lock_factory(),
            file_storage=file_storage,
            level_test_dao=level_test_dao,
            telegraph=create_telegraph(config.bot),
            message_manager=MessageManager(),
        )

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
