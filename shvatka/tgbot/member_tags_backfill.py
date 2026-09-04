import asyncio
import logging

from aiogram import Bot
from dishka import AsyncContainer

from shvatka.common import setup_logging
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.main_factory import create_dishka
from shvatka.tgbot.services.member_tags import MemberTagger

logger = logging.getLogger(__name__)

DELAY = 0.05
"""pause between players, telegram allows about 20 requests per second"""


async def main() -> None:
    paths = common_get_paths("BOT_PATH")

    setup_logging(paths)
    dishka: AsyncContainer = create_dishka("BOT_PATH")
    try:
        # bot is app-scoped and has to outlive the request scope it is used in
        await dishka.get(Bot)
        async with dishka() as request_container:
            dao = await request_container.get(HolderDao)
            tagger = await request_container.get(MemberTagger)
            await tag_all_players(dao, tagger)
    finally:
        await dishka.close()


async def tag_all_players(dao: HolderDao, tagger: MemberTagger, delay: float = DELAY) -> None:
    teams = await dao.team.get_teams()
    logger.info("tagging players of %s teams", len(teams))
    for team in teams:
        for team_player in await dao.team_player.get_players(team):
            if not team_player.player.has_user():
                continue
            await tagger.sync(team_player.player, team)
            await asyncio.sleep(delay)
    logger.info("all players tagged")


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
