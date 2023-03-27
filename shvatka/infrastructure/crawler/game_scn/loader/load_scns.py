import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO
from zipfile import Path as ZipPath

from aiogram import Bot
from dataclass_factory import Factory, Schema, NameStyle
from sqlalchemy.orm import close_all_sessions

from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models import dto
from shvatka.core.models import enums
from shvatka.core.models.dto import scn  # noqa: F401
from shvatka.core.services.game import upsert_game
from shvatka.core.services.scenario.scn_zip import unpack_scn
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.infrastructure.clients.factory import create_file_storage
from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.crawler.factory import get_paths
from shvatka.infrastructure.crawler.models.stat import GameStat
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.faсtory import create_pool, create_level_test_dao, create_redis
from shvatka.tgbot.config.parser.main import load_config
from shvatka.tgbot.main_factory import create_bot
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser

logger = logging.getLogger(__name__)


async def main():
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    dcf = Factory(default_schema=Schema(name_style=NameStyle.kebab))
    file_storage = create_file_storage(config.file_storage_config)
    bot = create_bot(config)
    Bot.set_current(bot)
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
                hint_parser=HintParser(
                    dao=dao.file_info,
                    file_storage=file_storage,
                    bot=bot,
                ),
                tech_chat_id=config.bot.log_chat,
            )
            bot_player = await dao.player.create_dummy()
            await dao.player.promote(bot_player, bot_player)
            bot_player.can_be_author = True
            await dao.commit()
            await load_scns(
                bot_player=bot_player,
                dao=dao,
                file_gateway=file_gateway,
                dcf=dcf,
                path=config.file_storage_config.path / "scn",
            )
    finally:
        await bot.session.close()
        close_all_sessions()


async def load_scns(
    bot_player: dto.Player,
    dao: HolderDao,
    file_gateway: FileGateway,
    dcf: Factory,
    path: Path,
):
    files = sorted((file for file in path.glob("*.zip")), key=lambda p: int(p.stem))
    for file in files:
        logger.info("loading game from file %s...", file.name)
        try:
            with file.open("rb") as game_zip_scn:
                game = await load_scn(
                    player=bot_player,
                    dao=dao,
                    file_gateway=file_gateway,
                    dcf=dcf,
                    zip_scn=game_zip_scn,
                )
                if not game:
                    continue
                results = load_results(game_zip_scn, dcf)
            await dao.game.set_completed(game)
            await set_results(game, results, dao)
            await dao.commit()

        except exceptions.CantEditGame:
            logger.info("game from file %s already loaded", file.name)
        else:
            logger.info("successfully loaded game %s with number %s", game.id, game.number)


async def set_results(game: dto.FullGame, results: GameStat, dao: HolderDao):
    game_start_at = add_timezone(results.start_at)
    await dao.game.set_start_at(game, game_start_at)
    await dao.game.set_number(game, results.id)
    for forum_team_name, levels in results.results.items():
        team = await dao.team.get_by_forum_team_name(forum_team_name)
        await dao.level_time.set_to_level(team, game, 0, game_start_at)
        for level in levels:
            await dao.level_time.set_to_level(team, game, level.number, add_timezone(level.at))
    for forum_team_name, keys in results.keys.items():
        team = await dao.team.get_by_forum_team_name(forum_team_name)
        for i, key in enumerate(keys):
            player = await get_or_create_player(dao, key.player)
            await join_team_if_already_not(player, team, game_start_at, dao)
            await add_waiver_if_already_not(player, team, game, dao)
            if i == len(keys) - 1:
                is_correct = True
            elif key.level != keys[i + 1].level:
                is_correct = True
            else:
                is_correct = False
            await dao.key_time.save_key(
                key=key.value,
                team=team,
                game=game,
                player=player,
                level=game.levels[key.level - 1],
                is_correct=is_correct,
                is_duplicate=False,
                at=add_timezone(key.at),
            )


def add_timezone(dt: datetime) -> datetime:
    return datetime.combine(dt.date(), dt.time(), tz_game)


async def get_or_create_player(dao: HolderDao, forum_player_name: str):
    player = await dao.player.get_by_forum_player_name(forum_player_name)
    if not player:
        player = await dao.player.create_for_forum_user_name(forum_player_name)
    return player


async def add_waiver_if_already_not(
    player: dto.Player, team: dto.Team, game: dto.Game, dao: HolderDao
):
    await dao.waiver.upsert_with_flush(
        dto.Waiver(
            player=player,
            team=team,
            game=game,
            played=enums.Played.yes,
        )
    )


async def join_team_if_already_not(
    player: dto.Player, team: dto.Team, at: datetime, dao: HolderDao
):
    current_team = await dao.team_player.get_team(player, for_date=at)
    if current_team is not None and current_team.id == team.id:
        return
    if current_team is not None:
        await dao.team_player.leave_team(player, at - timedelta(hours=8))
    await dao.team_player.join_team(
        player=player,
        team=team,
        role="Полевой",
        as_captain=False,
        joined_at=at - timedelta(hours=6),
    )


async def transfer_ownership(game: dto.FullGame, bot_player: dto.Player, dao: HolderDao):
    for guid in game.get_guids():
        await dao.file_info.transfer(guid, bot_player)
    for level in game.levels:
        await dao.level.transfer(level, bot_player)
    await dao.game.transfer(game, bot_player)


def load_results(game_zip_scn: BinaryIO, dcf: Factory) -> GameStat:
    zip_path = ZipPath(game_zip_scn)
    for unpacked_file in zip_path.iterdir():
        if not unpacked_file.is_file():
            continue
        if unpacked_file.name != "results.json":
            continue
        with unpacked_file.open("r", encoding="utf8") as results_file:
            results = dcf.load(json.load(results_file), GameStat)
        return results
    raise ValueError("no results found")


async def load_scn(
    player: dto.Player,
    dao: HolderDao,
    file_gateway: FileGateway,
    dcf: Factory,
    zip_scn: BinaryIO,
) -> dto.FullGame | None:
    try:
        with unpack_scn(ZipPath(zip_scn)).open() as scenario:  # type: scn.RawGameScenario
            game = await upsert_game(scenario, player, dao.game_upserter, dcf, file_gateway)
    except exceptions.ScenarioNotCorrect as e:
        logger.error("game scenario from player %s has problems", player.id, exc_info=e)
        return None
    logger.info("game scenario with id %s saved", game.id)
    return game


if __name__ == "__main__":
    asyncio.run(main())
