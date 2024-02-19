import asyncio

from sqlalchemy.orm import close_all_sessions

from shvatka.common import setup_logging
from shvatka.infrastructure.clients.factory import create_file_storage
from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.factory import create_pool, create_level_test_dao, create_redis
from shvatka.tgbot.config.parser.main import load_config
from shvatka.tgbot.main_factory import get_paths, create_bot


async def main():
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    file_storage = create_file_storage(config.file_storage_config)
    bot = create_bot(config.bot)
    pool = create_pool(config.db)
    level_test_dao = create_level_test_dao()
    try:
        async with (
            pool() as session,
            create_redis(config.redis) as redis,
        ):
            dao = HolderDao(session, redis, level_test_dao)
            file_gateway = BotFileGateway(
                bot=bot,
                file_storage=file_storage,
                dao=dao.file_info,
                tech_chat_id=config.bot.log_chat,
            )
            await fill_all_file_id(dao.file_info, file_gateway)
    finally:
        await bot.session.close()
        close_all_sessions()


async def fill_all_file_id(dao: FileInfoDao, file_gateway: BotFileGateway):
    while batch := await dao.get_without_file_id(100):
        for file in batch:
            await file_gateway.renew_file_id(file.author, file)
        await dao.commit()


if __name__ == "__main__":
    asyncio.run(main())
