import asyncio
from pathlib import Path

from dataclass_factory import Factory
from sqlalchemy.orm import close_all_sessions

from api.main_factory import get_paths
from common.config.parser.logging_config import setup_logging
from common.factory import create_dataclass_factory
from infrastructure.db.dao.holder import HolderDao
from infrastructure.db.faсtory import create_pool, create_level_test_dao, create_redis
from tgbot.config.parser.main import load_config


async def main(path: Path):
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    dcf = create_dataclass_factory()
    pool = create_pool(config.db)
    level_test_dao = create_level_test_dao()
    try:
        async with (
            pool() as session,
            create_redis(config.redis) as redis,
        ):
            dao = HolderDao(session, redis, level_test_dao)
            await load_teams(path, dao, dcf)
    finally:
        close_all_sessions()


async def load_teams(path: Path, dao: HolderDao, dcf: Factory):
    pass


if __name__ == "__main__":
    asyncio.run(main(Path(__file__).parent / "teams.json"))
