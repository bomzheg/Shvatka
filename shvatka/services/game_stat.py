from shvatka.dal.key_log import TypedKeyGetter
from shvatka.dal.level_times import GameStatDao
from shvatka.models import dto
from shvatka.models.dto.levels_times import GameStat


async def get_typed_keys(game: dto.Game, dao: TypedKeyGetter) -> dict[dto.Team, list[dto.KeyTime]]:
    return await dao.get_typed_keys(game)


async def get_game_stat(game: dto.Game, dao: GameStatDao):
    """return sorted by level number grouped by teams stat"""
    level_times = await dao.get_game_level_times(game)
    result = {}
    for lt in level_times:
        result.setdefault(lt.team, []).append(lt)
    return GameStat(level_times=result)
