from shvatka.dal.organizer import GameOrgsGetter
from shvatka.models import dto


async def get_orgs(game: dto, dao: GameOrgsGetter) -> list[dto.Organizer]:
    return [dto.PrimaryOrganizer(player=game.author, game=game), *await dao.get_orgs(game)]
