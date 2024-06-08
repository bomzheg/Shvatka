from aiogram.types import Message

from shvatka.core.models import dto
from shvatka.core.services.organizers import get_by_player
from shvatka.infrastructure.db.dao.holder import HolderDao


async def is_org_on_running_game(_: Message, player: dto.Player, game: dto.Game, dao: HolderDao):
    if game is None or not game.is_started():
        return False
    return await is_org(_, player=player, game=game, dao=dao)


async def is_org(_: Message, player: dto.Player, game: dto.Game, dao: HolderDao):
    org = await get_by_player(player=player, game=game, dao=dao.organizer)
    if org is None or org.deleted:
        return False
    return {"org": org}
