from typing import Iterable

from shvatka.dal.organizer import GameOrgsGetter
from shvatka.models import dto
from shvatka.utils.exceptions import PermissionsError, GameHasAnotherAuthor


async def get_orgs(game: dto, dao: GameOrgsGetter) -> Iterable[dto.Organizer]:
    return [dto.PrimaryOrganizer(player=game.author, game=game), *await dao.get_orgs(game)]


async def get_secondary_orgs(game: dto.Game, dao: GameOrgsGetter) -> Iterable[dto.SecondaryOrganizer]:
    return await dao.get_orgs(game)


def check_allow_add_orgs(game: dto.Game, manage_token: str, inviter: dto.Player):
    if game.manage_token != manage_token:
        raise PermissionsError(permission_name="add_game_organizer", player=inviter, game=game)
    if game.author.id != inviter.id:
        raise GameHasAnotherAuthor(game=game, player=inviter, alarm=True)

