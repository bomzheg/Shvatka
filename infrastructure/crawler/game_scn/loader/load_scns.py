import asyncio
import json
import logging
from pathlib import Path
from zipfile import Path as ZipPath

from aiogram import Bot
from dataclass_factory import Factory
from sqlalchemy.orm import close_all_sessions
from typing.io import BinaryIO

from common.config.models.paths import Paths
from common.config.parser.logging_config import setup_logging
from common.config.parser.paths import common_get_paths
from common.factory import create_dataclass_factory
from infrastructure.clients.factory import create_file_storage
from infrastructure.clients.file_gateway import BotFileGateway
from infrastructure.crawler.models.stat import GameStat
from infrastructure.db.dao.holder import HolderDao
from infrastructure.db.faсtory import create_pool, create_level_test_dao, create_redis
from shvatka.interfaces.clients.file_storage import FileGateway
from shvatka.models import dto, enums
from shvatka.services.game import upsert_game
from shvatka.services.scenario.scn_zip import unpack_scn
from shvatka.utils import exceptions
from tgbot.config.parser.main import load_config
from tgbot.main_factory import create_bot
from tgbot.views.hint_factory.hint_parser import HintParser

logger = logging.getLogger(__name__)


async def main(path: Path):
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    dcf = create_dataclass_factory()
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
            )
            tech_player = await dao.player.upsert_player(
                await dao.user.upsert_user(
                    dto.User(
                        tg_id=config.bot.log_chat,
                        first_name="SYSTEM",
                        last_name="PARSED UPLOADER",
                        is_bot=True,
                    )
                )
            )
            await dao.player.promote(tech_player, tech_player)
            tech_player.can_be_author = True
            bot_player = await dao.player.upsert_player(
                await dao.user.upsert_user(
                    dto.User(
                        tg_id=bot.id,
                        first_name="SYSTEM",
                        last_name="PARSER",
                        is_bot=True,
                    )
                )
            )
            await dao.player.promote(bot_player, bot_player)
            bot_player.can_be_author = True
            await dao.commit()
            await load_scns(
                tech_player=tech_player,
                bot_player=bot_player,
                dao=dao,
                file_gateway=file_gateway,
                dcf=dcf,
                path=path,
            )
    finally:
        await bot.session.close()
        close_all_sessions()


async def load_scns(
    tech_player: dto.Player,
    bot_player: dto.Player,
    dao: HolderDao,
    file_gateway: FileGateway,
    dcf: Factory,
    path: Path,
):
    for file in path.glob("*.zip"):
        logger.info("loading game from file %s", file.name)
        try:
            with file.open("rb") as game_zip_scn:
                game = await load_scn(
                    player=tech_player,
                    dao=dao,
                    file_gateway=file_gateway,
                    dcf=dcf,
                    zip_scn=game_zip_scn,
                )
                if not game:
                    continue
                await dao.game.set_completed(game)
                game.status = enums.GameStatus.complete
                results = load_results(game_zip_scn, dcf)
            await dao.game.set_start_at(game, results.start_at)
            game.start_at = results.start_at
            await dao.game.set_number(game, results.id)
            game.number = results.id
            await transfer_ownership(game, bot_player, dao)
            await dao.commit()

        except exceptions.CantEditGame:
            logger.info("game from file %s already loaded", file.name)
        else:
            logger.info("successfully loaded game %s with number %s", game.id, game.number)


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


async def load_scn(
    player: dto.Player,
    dao: HolderDao,
    file_gateway: FileGateway,
    dcf: Factory,
    zip_scn: BinaryIO,
) -> dto.FullGame | None:
    try:
        with unpack_scn(ZipPath(zip_scn)).open() as scn:
            game = await upsert_game(scn, player, dao.game_upserter, dcf, file_gateway)
    except exceptions.ScenarioNotCorrect as e:
        logger.error("game scenario from player %s has problems", player.id, exc_info=e)
        return
    logger.info("game scenario with id %s saved", game.id)
    return game


def get_paths() -> Paths:
    return common_get_paths("CRAWLER_PATH")


if __name__ == "__main__":
    asyncio.run(main(Path(__name__).parent / "scn"))
