from datetime import datetime

from adaptix import Retort

from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.interfaces.dal.complex import GameCompleter, GamePackager
from shvatka.core.interfaces.dal.game import (
    GameUpserter,
    GameCreator,
    GameAuthorsFinder,
    GameByIdGetter,
    ActiveGameFinder,
    WaiverStarter,
    GameStartPlanner,
    GameNameChecker,
    GameRenamer,
    CompletedGameFinder,
    PreviewGameByIdGetter,
)
from shvatka.core.interfaces.dal.level import LevelLinker
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto
from shvatka.core.models.dto import scn, export_stat
from shvatka.core.rules.game import check_can_read, check_game_editable
from shvatka.core.rules.level import (
    check_is_author as check_is_level_author,
    check_can_link_to_game,
)
from shvatka.core.services.player import check_allow_be_author
from shvatka.core.services.scenario.files import upsert_files, get_file_metas, get_file_contents
from shvatka.core.services.scenario.game_ops import parse_uploaded_game, check_all_files_saved
from shvatka.core.utils import exceptions
from shvatka.core.utils.exceptions import AnotherGameIsActive, CantEditGame


async def upsert_game(
    raw_scn: scn.RawGameScenario,
    author: dto.Player,
    dao: GameUpserter,
    dcf: Retort,
    file_gateway: FileGateway,
) -> dto.FullGame:
    check_allow_be_author(author)
    game_scn = parse_uploaded_game(raw_scn, dcf)
    if not await dao.is_name_available(name=game_scn.name):
        if not await dao.is_author_game_by_name(name=game_scn.name, author=author):
            raise CantEditGame(
                player=author, text=f"cant edit game with name {game_scn.name} (not author)"
            )
        game = await dao.get_game_by_name(name=game_scn.name, author=author)
        check_game_editable(game)
    guids = await upsert_files(author, raw_scn.files, game_scn.files, dao, file_gateway)
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
    levels: list[dto.Level] | None = None,
) -> dto.Game:
    if levels is None:
        levels = []
    check_allow_be_author(author)
    await check_new_game_name_available(name=name, author=author, dao=dao)
    game = await dao.create_game(author, name)
    for level in levels:
        check_can_link_to_game(game, level)
        await dao.link_to_game(level, game)
    await dao.commit()
    return game


async def get_authors_games(
    author: dto.Player,
    dao: GameAuthorsFinder,
) -> list[dto.Game]:
    check_allow_be_author(author)
    return await dao.get_all_by_author(author)


async def get_completed_games(dao: CompletedGameFinder) -> list[dto.Game]:
    return await dao.get_completed_games()


async def add_level(game: dto.Game, level: dto.Level, author: dto.Player, dao: LevelLinker):
    check_allow_be_author(author)
    check_can_read(game=game, player=author)
    check_game_editable(game=game)
    check_is_level_author(level=level, player=author)
    check_can_link_to_game(game=game, level=level, author=author)
    await dao.link_to_game(level=level, game=game)
    await dao.commit()


async def get_game(id_: int, *, author: dto.Player | None = None, dao: GameByIdGetter) -> dto.Game:
    return await dao.get_by_id(id_=id_, author=author)


async def get_preview_game(
    id_: int, *, author: dto.Player | None = None, dao: PreviewGameByIdGetter
) -> dto.PreviewGame:
    return await dao.get_preview(id_=id_, author=author)


async def get_full_game(id_: int, author: dto.Player, dao: GameByIdGetter) -> dto.FullGame:
    game = await dao.get_full(id_=id_)
    check_can_read(game, author)
    return game


async def get_game_package(
    id_: int,
    author: dto.Player,
    dao: GamePackager,
    dcf: Retort,
    file_gateway: FileGateway,
) -> scn.RawGameScenario:
    game = await dao.get_full(id_=id_)
    check_can_read(game, author)
    file_metas = await get_file_metas(game, author, dao)
    contents = await get_file_contents(file_metas, file_gateway)
    scenario = scn.FullGameScenario(
        name=game.name, levels=[level.scenario for level in game.levels], files=file_metas
    )
    if game.is_complete():
        assert game.start_at
        game_stat = export_stat.GameStat(
            id=id_,
            start_at=game.start_at,
            results={
                key.name: [export_stat.LevelTime.from_dto(lt) for lt in value]
                for key, value in (
                    await dao.get_game_level_times_by_teams(game, len(game.levels))
                ).items()
            },
            keys={
                key.name: [export_stat.Key.from_dto(k) for k in value]
                for key, value in (await dao.get_typed_keys_grouped(game)).items()
            },
            waivers=[export_stat.Waiver.from_dto(w) for w in await dao.get_all_by_game(game)],
            team_identity=export_stat.TeamIdentity.bomzheg_engine_name,
        )
    else:
        game_stat = None
    return scn.RawGameScenario(scn=dcf.dump(scenario), files=contents, stat=dcf.dump(game_stat))


async def get_active(dao: ActiveGameFinder) -> dto.Game | None:
    return await dao.get_active_game()


async def rename_game(author: dto.Player, game: dto.Game, new_name: str, dao: GameRenamer):
    check_can_read(game, author)
    check_game_editable(game)
    await dao.rename_game(game, new_name)
    await dao.commit()


async def start_waivers(game: dto.Game, author: dto.Player, dao: WaiverStarter):
    check_allow_be_author(author)
    check_can_read(game, author)
    check_game_editable(game)
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
    check_can_read(game, author)
    check_game_editable(game)
    await check_no_other_game_active(dao, game)
    await dao.set_start_at(game, start_at)
    game.start_at = start_at
    await scheduler.cancel_scheduled_game(game)

    await scheduler.plain_prepare(game)
    await scheduler.plain_start(game)

    await dao.commit()


async def cancel_planed_start(
    game: dto.Game, author: dto.Player, scheduler: Scheduler, dao: GameStartPlanner
):
    check_can_read(game, author)
    check_game_editable(game)
    await dao.cancel_start(game)
    game.start_at = None
    await scheduler.cancel_scheduled_game(game)
    await dao.commit()


async def complete_game(game: dto.Game, dao: GameCompleter):
    if not game.is_finished():
        raise exceptions.GameNotFinished(game=game)
    await dao.set_number(game, await dao.get_max_number() + 1)
    await dao.set_completed(game)
    await dao.commit()


async def check_no_other_game_active(dao: ActiveGameFinder, game: dto.Game):
    if (other_game := await dao.get_active_game()) and game.id != other_game.id:
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
