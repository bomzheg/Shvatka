from shvatka.core.interfaces.dal.key_log import TypedKeyGetter
from shvatka.core.interfaces.dal.level_times import GameStatDao
from shvatka.core.models import dto
from shvatka.core.services.organizers import get_by_player, check_can_see_log_keys, check_can_spy


async def get_typed_keys(
    game: dto.Game,
    player: dto.Player,
    dao: TypedKeyGetter,
) -> dict[dto.Team, list[dto.KeyTime]]:
    org = await get_by_player(game=game, player=player, dao=dao)
    check_can_see_log_keys(org)
    keys = await dao.get_typed_keys(game)
    grouped: dict[dto.Team, list[dto.KeyTime]] = {}
    for key in keys:
        grouped.setdefault(key.team, []).append(key)
    return grouped


async def get_game_stat(game: dto.Game, player: dto.Player, dao: GameStatDao) -> dto.GameStat:
    """return sorted by level number grouped by teams stat"""
    org = await get_by_player(game=game, player=player, dao=dao)
    check_can_spy(org)
    level_times = await dao.get_game_level_times(game)
    levels_count = await dao.get_max_level_number(game)
    result: dict[dto.Team, list[dto.LevelTimeOnGame]] = {}
    for lt in level_times:
        result.setdefault(lt.team, []).append(lt.to_on_game(levels_count))
    return dto.GameStat(level_times=result)


async def get_game_spy(game: dto.Game, player: dto.Player, dao: GameStatDao):
    stat = await get_game_stat(game, player, dao)
    result = []
    for team, lts in stat.level_times.items():
        result.append(lts[-1])
    return result
