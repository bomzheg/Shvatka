import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from dataclass_factory import Factory
from sqlalchemy.orm import close_all_sessions

from src.api.main_factory import get_paths
from src.common.config.parser.logging_config import setup_logging
from src.common.factory import create_dataclass_factory
from src.infrastructure.crawler.models.team import ParsedTeam
from src.infrastructure.db.dao.holder import HolderDao
from src.infrastructure.db.faсtory import create_pool, create_level_test_dao, create_redis
from src.shvatka.utils import exceptions
from src.shvatka.utils.datetime_utils import tz_utc
from src.tgbot.config.parser.main import load_config

logger = logging.getLogger(__name__)


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
    with path.open(encoding="utf8") as f:
        teams = dcf.load(json.load(f), list[ParsedTeam])
    for team in teams:
        logger.info("loading team %s", team.name)
        await save_team(team, False, dao)
    await dao.commit()


async def save_team(parsed_team: ParsedTeam, with_team_players: bool, dao: HolderDao):
    saved_team = await dao.forum_team.upsert(parsed_team)
    players = {}
    captain = None
    for parsed_player in parsed_team.players:
        saved_player = await dao.forum_user.upsert(parsed_player)
        player = await dao.player.create_for_forum_user(saved_player)
        players[parsed_player] = player
        if parsed_player.role == "Капитан":
            captain = parsed_player
    team = await dao.team.create_by_forum(saved_team, players.get(captain, None))
    if with_team_players:
        for parsed_player, saved_player in players.items():
            try:
                team_player = await dao.team_player.get_team_player(saved_player)
            except exceptions.PlayerNotInTeam:
                pass
            else:
                if team_player.team_id == team.id:
                    await dao.team_player.change_role(team_player, parsed_player.role)
                    continue
                else:
                    await dao.team_player.leave_team(
                        saved_player, datetime.now(tz=tz_utc) - timedelta(hours=2)
                    )
                    #  no return - need to join
            await dao.team_player.join_team(
                player=saved_player,
                team=team,
                role=parsed_player.role,
                as_captain=((captain == parsed_player) if captain else False),
                joined_at=datetime.now(tz=tz_utc),
            )


if __name__ == "__main__":
    asyncio.run(main(Path(__file__).parent / "teams.json"))
