import asyncio
import logging

from dishka import make_async_container

from shvatka.common import setup_logging
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.di import get_providers
from shvatka.infrastructure.di.infra import get_infra_only_providers

logger = logging.getLogger(__name__)


async def main():
    paths = common_get_paths("INFRA_PATH")

    setup_logging(paths)
    dishka = make_async_container(
        *get_providers("INFRA_PATH"),
        *get_infra_only_providers(),
    )
    try:
        dao = await dishka.get(HolderDao)
        await renew_id_usernames(dao)
    finally:
        await dishka.close()


async def renew_id_usernames(dao: HolderDao) -> list[tuple[str, str]]:
    """Give players with an `id{id}` username a name-based one instead.

    Players are renamed only if their telegram or forum identity provides a free
    username, so those without any name keep the id-based one.
    """
    renamed = await dao.player.renew_id_usernames()
    for old, new in renamed:
        logger.info("username %s renewed to %s", old, new)
    await dao.commit()
    logger.info("renewed %s usernames", len(renamed))
    return renamed


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
