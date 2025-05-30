from shvatka.core.interfaces.dal.complex import TypedKeyGetter, GameStatDao
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.services.organizers import get_by_player, check_can_see_log_keys, check_can_spy


async def get_typed_keys(
    game: dto.Game,
    identity: IdentityProvider,
    dao: TypedKeyGetter,
) -> dict[dto.Team, list[dto.KeyTime]]:
    if not game.is_complete():
        player = await identity.get_required_player()
        org = await get_by_player(game=game, player=player, dao=dao)
        check_can_see_log_keys(org)
    return await dao.get_typed_keys_grouped(game)


async def get_game_stat(
    game: dto.Game, identity: IdentityProvider, dao: GameStatDao
) -> dto.GameStat:
    """return sorted by level number grouped by teams stat"""
    player = await identity.get_required_player()
    if not game.is_complete():
        org = await get_by_player(game=game, player=player, dao=dao)
        check_can_spy(org)
    result = await dao.get_game_level_times_by_teams(game)
    return dto.GameStat(level_times=result)


async def get_game_stat_with_hints(
    game: dto.Game, player: dto.Player, dao: GameStatDao
) -> dto.GameStatWithHints:
    """return sorted by level number grouped by teams stat"""
    if not game.is_complete():
        org = await get_by_player(game=game, player=player, dao=dao)
        check_can_spy(org)
    full_game = await dao.add_levels(game)
    result = await dao.get_game_level_times_with_hints(full_game)
    return dto.GameStatWithHints(level_times=result)


async def get_game_spy(
    game: dto.Game, player: dto.Player, dao: GameStatDao
) -> list[dto.LevelTimeOnGame]:
    stat = await get_game_stat_with_hints(game, player, dao)
    return [lts[-1] for lts in stat.level_times.values()]
