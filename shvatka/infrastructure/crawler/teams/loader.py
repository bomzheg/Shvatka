import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from dataclass_factory import Factory
from sqlalchemy.orm import close_all_sessions

from shvatka.api.main_factory import get_paths
from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.common.factory import create_dataclass_factory
from shvatka.core.models import dto, enums
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.crawler.game_scn.common import UNPARSEABLE_GAMES
from shvatka.infrastructure.crawler.models.team import ParsedTeam, ParsedPlayer
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.factory import create_pool, create_level_test_dao, create_redis
from shvatka.tgbot.config.parser.main import load_config

logger = logging.getLogger(__name__)
WITH_TEAM_PLAYERS = False


async def main(with_team_players: bool):
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    path = config.file_storage_config.path.parent / "teams.json"
    dcf = create_dataclass_factory()
    pool = create_pool(config.db)
    level_test_dao = create_level_test_dao()
    try:
        async with (
            pool() as session,
            create_redis(config.redis) as redis,
        ):
            dao = HolderDao(session, redis, level_test_dao)
            await load_teams(path, with_team_players, dao, dcf)
    finally:
        close_all_sessions()


async def load_teams(path: Path, with_team_players: bool, dao: HolderDao, dcf: Factory):
    with path.open(encoding="utf8") as f:
        teams = dcf.load(json.load(f), list[ParsedTeam])
    for team in teams:
        logger.info("loading team %s", team.name)
        await save_team(team, with_team_players, dao)
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
            await add_waivers(parsed_player, saved_player, dao)
            try:
                team_player = await dao.team_player.get_team_player(saved_player)
            except exceptions.PlayerNotInTeam:
                pass
            else:
                if team_player.team_id == team.id:
                    await dao.team_player.change_role(team_player, parsed_player.role)
                    continue
                else:  # noqa: RET507
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


async def add_waivers(
    parsed_player: ParsedPlayer, saved_player: dto.Player, dao: HolderDao
) -> None:
    for game_number in parsed_player.games:
        if game_number in UNPARSEABLE_GAMES:
            continue
        if await dao.waiver.is_player_played(saved_player, game_number):
            continue
        logger.debug(
            "adding %s for player %s (%s)",
            game_number,
            saved_player.name_mention,
            saved_player.id,
        )
        game = await dao.game.get_game_by_number(game_number)
        assert game.start_at is not None
        team_for_game = await dao.team_player.get_team(saved_player, game.start_at)
        if not team_for_game or not await dao.waiver.is_team_played(team_for_game, game_number):
            next_tp = await dao.team_player.get_next_team_player(
                player=saved_player, at=game.start_at
            )
            if not next_tp:
                logger.warning(
                    "don't know how to chose team for player %s "
                    "for game number %s. next team is None",
                    saved_player.name_mention,
                    game_number,
                )
                continue
            if not await dao.waiver.is_team_played(next_tp.team, game_number):
                logger.warning(
                    "don't know how to chose team for player %s "
                    "for game number %s. "
                    "next team (from %s) is %s, "
                    "but this team not played too",
                    saved_player.name_mention,
                    game_number,
                    next_tp.date_joined,
                    next_tp.team,
                )
                continue
            if not team_for_game:
                await dao.team_player.change_date_joined(
                    next_tp, game.start_at - timedelta(hours=5)
                )
                team_for_game = next_tp.team
            else:
                logger.warning(
                    "how to change %s to %s for %s", team_for_game, next_tp.team, game.start_at
                )
                continue
        waiver = dto.Waiver(
            player=saved_player, team=team_for_game, game=game, played=enums.Played.yes
        )
        await dao.waiver.upsert(waiver)
        logger.info(
            "added waiver for player %s for game number %s team is %s",
            saved_player.name_mention,
            game_number,
            team_for_game,
        )


if __name__ == "__main__":
    asyncio.run(main(WITH_TEAM_PLAYERS))
