from shvatka.dal.key_log import TypedKeyGetter
from shvatka.dal.level_times import GameStatDao
from shvatka.models import dto
from shvatka.models.dto.levels_times import GameStat


async def get_typed_keys(game: dto.Game, dao: TypedKeyGetter) -> dict[dto.Team, list[dto.KeyTime]]:
    keys = await dao.get_typed_keys(game)
    grouped = {}
    for key in keys:
        grouped.setdefault(key.team, []).append(key)
    return grouped


async def get_game_stat(game: dto.Game, dao: GameStatDao):
    """return sorted by level number grouped by teams stat"""
    level_times = await dao.get_game_level_times(game)
    levels_count = await dao.get_max_level_number(game)
    result = {}
    for lt in level_times:
        result.setdefault(lt.team, []).append(lt.to_on_game(levels_count))
    return GameStat(level_times=result)


async def get_game_spy(game: dto.Game, dao: GameStatDao):
    stat = await get_game_stat(game, dao)
    result = []
    for team, lts in stat.level_times.items():
        result.append(lts[-1])
    return result
