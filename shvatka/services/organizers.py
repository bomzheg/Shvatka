from typing import Iterable

from shvatka.dal.organizer import GameOrgsGetter
from shvatka.models import dto


async def get_orgs(game: dto, dao: GameOrgsGetter) -> Iterable[dto.Organizer]:
    return [dto.PrimaryOrganizer(player=game.author, game=game), *await dao.get_orgs(game)]


async def get_secondary_orgs(game: dto.Game, dao: GameOrgsGetter) -> Iterable[dto.SecondaryOrganizer]:
    return await dao.get_orgs(game)
