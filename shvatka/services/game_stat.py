from shvatka.dal.key_log import TypedKeyGetter
from shvatka.models import dto


async def get_typed_keys(game: dto.Game, dao: TypedKeyGetter) -> dict[dto.Team, list[dto.KeyTime]]:
    return await dao.get_typed_keys(game)
