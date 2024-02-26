import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Any, Callable, Coroutine
from zipfile import Path as ZipPath

from dataclass_factory import Factory
from dishka import make_async_container

from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.common.config.parser.paths import common_get_paths
from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.models import dto
from shvatka.core.models import enums
from shvatka.core.models.dto import scn  # noqa: F401
from shvatka.core.models.dto.export_stat import (
    GameStat,
    TeamIdentity,
    Player,
    PlayerIdentity,
)
from shvatka.core.services.game import upsert_game
from shvatka.core.services.scenario.scn_zip import unpack_scn
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import add_timezone, tz_utc
from shvatka.infrastructure.db.dao import TeamDao
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.di import get_providers
from shvatka.tgbot.config.models.main import TgBotConfig

logger = logging.getLogger(__name__)


async def main():
    paths = common_get_paths("CRAWLER_PATH")

    setup_logging(paths)
    dishka = make_async_container(
        *get_providers("CRAWLER_PATH"),
    )
    try:
        config = await dishka.get(TgBotConfig)
        dao = await dishka.get(HolderDao)
        file_gateway = await dishka.get(FileGateway)
        bot_player = await dao.player.upsert_author_dummy()
        await dao.commit()
        await load_scns(
            bot_player=bot_player,
            dao=dao,
            file_gateway=file_gateway,
            dcf=await dishka.get(Factory),
            path=config.file_storage_config.path.parent / "scn",
        )
    finally:
        await dishka.close()


async def load_scns(
    bot_player: dto.Player,
    dao: HolderDao,
    file_gateway: FileGateway,
    dcf: Factory,
    path: Path,
):
    files = sorted(path.glob("*.zip"), key=lambda p: int(p.stem))
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
    game_start_at = add_timezone(results.start_at, timezone=tz_utc)
    await dao.game.set_start_at(game, game_start_at)
    await dao.game.set_number(game, results.id)
    team_getter = get_team_getter(dao.team, results.team_identity)
    for team_name, levels in results.results.items():
        team = await team_getter(team_name)
        for level in levels:
            if level.at is not None:
                await dao.level_time.set_to_level(
                    team, game, level.number, add_timezone(level.at, timezone=tz_utc)
                )
    for team_name, keys in results.keys.items():
        team = await team_getter(team_name)
        for i, key in enumerate(keys):  # type: int, dto.export_stat.Key
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
                type_=enums.KeyType.simple if is_correct else enums.KeyType.wrong,
                is_duplicate=False,
                at=add_timezone(key.at, timezone=tz_utc),
            )


def get_team_getter(
    dao: TeamDao, team_identity: TeamIdentity
) -> Callable[[str], Coroutine[Any, Any, dto.Team]]:
    match team_identity:
        case TeamIdentity.bomzheg_engine_name:
            team_getter = dao.get_by_name
        case TeamIdentity.forum_name:
            team_getter = dao.get_by_forum_team_name
        case _:
            team_getter = dao.get_by_forum_team_name
    return team_getter


async def get_or_create_player(dao: HolderDao, player: Player):
    match player.identity:
        case PlayerIdentity.forum_name:
            result = await dao.player.get_by_forum_player_name(player.forum_name)
            if not result:
                result = await dao.player.create_for_forum_user_name(player.forum_name)
            return result
        case PlayerIdentity.tg_user_id:
            try:
                return await dao.player.get_by_user_id(player.tg_user_id)
            except exceptions.PlayerNotFoundError:
                return await dao.player.create_for_user(
                    await dao.user.upsert_user(dto.User(tg_id=player.tg_user_id))
                )


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
