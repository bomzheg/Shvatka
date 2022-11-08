from datetime import datetime

from dataclass_factory import Factory

from shvatka.clients.file_storage import FileStorage
from shvatka.dal.game import (
    GameUpserter, GameCreator, GameAuthorsFinder, GameByIdGetter,
    ActiveGameFinder, WaiverStarter, GameStartPlanner, GameNameChecker,
)
from shvatka.models import dto
from shvatka.models.dto.scn.game import RawGameScenario
from shvatka.scheduler import Scheduler
from shvatka.services.player import check_allow_be_author
from shvatka.services.scenario.files import upsert_files
from shvatka.services.scenario.game_ops import parse_uploaded_game, check_all_files_saved
from shvatka.utils.exceptions import NotAuthorizedForEdit, AnotherGameIsActive, CantEditGame


async def upsert_game(
    raw_scn: RawGameScenario, author: dto.Player,
    dao: GameUpserter, dcf: Factory, file_storage: FileStorage,
) -> dto.FullGame:
    check_allow_be_author(author)
    game_scn = parse_uploaded_game(raw_scn.scn, dcf)
    if not await dao.is_name_available(name=game_scn.name):
        if not await dao.is_author_game_by_name(name=game_scn.name, author=author):
            raise CantEditGame(player=author, text=f"cant edit game with name {game_scn.name}")
    guids = await upsert_files(author, raw_scn.files, game_scn.files, dao, file_storage)
    check_all_files_saved(game=game_scn, guids=guids)
    game = await dao.upsert_game(author, game_scn)
    await dao.unlink_all(game)
    levels = []
    for number, level in enumerate(game_scn.levels):
        saved_level = await dao.upsert(author, level, game, number)
        levels.append(saved_level)
    await dao.commit()
    return game.to_full_game(levels)


async def create_game(
    author: dto.Player,
    name: str,
    dao: GameCreator,
    levels: list[dto.Level] = None,
) -> dto.Game:
    check_allow_be_author(author)
    await check_new_game_name_available(name=name, author=author, dao=dao)
    game = await dao.create_game(author, name)
    for level in levels:
        await dao.link_to_game(level, game)
    await dao.commit()
    return game


async def get_authors_games(
    author: dto.Player, dao: GameAuthorsFinder,
) -> list[dto.Game]:
    check_allow_be_author(author)
    return await dao.get_all_by_author(author)


async def get_game(id_: int, author: dto.Player, dao: GameByIdGetter) -> dto.Game:
    return await dao.get_by_id(id_, author)


async def get_active(dao: ActiveGameFinder) -> dto.Game:
    return await dao.get_active_game()


async def start_waivers(game: dto.Game, author: dto.Player, dao: WaiverStarter):
    check_allow_be_author(author)
    check_is_author(game, author)
    await check_no_game_active(dao)
    await dao.start_waivers(game)
    await dao.commit()


async def plain_start(
    game: dto.Game,
    author: dto.Player,
    start_at: datetime,
    dao: GameStartPlanner,
    scheduler: Scheduler,
):
    check_allow_be_author(author)
    check_is_author(game, author)
    await check_no_other_game_active(dao, game)
    await dao.set_start_at(game, start_at)
    game.start_at = start_at

    await scheduler.plain_prepare(game)
    await scheduler.plain_start(game)

    await dao.commit()


async def check_no_other_game_active(dao: ActiveGameFinder, game: dto.Game):
    if other_game := await dao.get_active_game():
        if game.id != other_game.id:
            raise AnotherGameIsActive(
                game=game,
                game_status=game.status,
            )


async def check_no_game_active(dao: ActiveGameFinder):
    if game := await dao.get_active_game():
        raise AnotherGameIsActive(
            game=game,
            game_status=game.status,
        )


async def check_new_game_name_available(name: str, author: dto.Player, dao: GameNameChecker):
    if not await dao.is_name_available(name):
        raise CantEditGame(text="другая игра имеет такое имя", player=author)


def check_is_author(game: dto.Game, player: dto.Player):
    if not game.is_author_id(player.id):
        raise NotAuthorizedForEdit(
            permission_name="game_edit", player=player, game=game,
        )
