from shvatka.dal.organizer import GameOrgsGetter, OrgAdder, OrgByIdGetter
from shvatka.dal.secure_invite import InviteSaver, InviteRemover
from shvatka.models import dto
from shvatka.services.game import get_game
from shvatka.utils.exceptions import PermissionsError, GameHasAnotherAuthor, SaltError
from shvatka.views.game import OrgNotifier, NewOrg


async def get_orgs(game: dto.Game, dao: GameOrgsGetter) -> list[dto.Organizer]:
    return [dto.PrimaryOrganizer(player=game.author, game=game), *await dao.get_orgs(game)]


async def get_spying_orgs(game: dto.Game, dao: GameOrgsGetter) -> list[dto.Organizer]:
    return [org for org in await get_orgs(game, dao) if org.can_spy]


async def get_secondary_orgs(game: dto.Game, dao: GameOrgsGetter) -> list[dto.SecondaryOrganizer]:
    return await dao.get_orgs(game)


def check_allow_add_orgs(game: dto.Game, inviter_id: int):
    if game.author.id != inviter_id:
        raise GameHasAnotherAuthor(game=game, player_id=inviter_id, alarm=True)


def check_game_token(game: dto.Game, manage_token: str):
    if game.manage_token != manage_token:
        raise PermissionsError(permission_name="add_game_organizer", game=game)


async def save_invite_to_orgs(game: dto.Game, inviter: dto.Player, dao: InviteSaver) -> str:
    return await dao.save_new_invite(dct=dict(game_id=game.id, inviter_id=inviter.id))


async def dismiss_to_be_org(token: str, dao: InviteRemover):
    await dao.remove_invite(token)


async def agree_to_be_org(
    token: str,
    inviter_id: int,
    player: dto.Player,
    org_notifier: OrgNotifier,
    dao: OrgAdder,
):
    data = await dao.get_invite(token)
    if data["inviter_id"] != inviter_id:
        raise SaltError(text="Ошибка нарушения данных. токен в зашифрованной и открытой части не совпал", alarm=True)
    game = await get_game(id_=data["game_id"], dao=dao)
    check_allow_add_orgs(game, inviter_id)
    org = await dao.add_new_org(game, player)
    await dao.commit()
    await org_notifier.notify(NewOrg(orgs_list=await get_orgs(game, dao), game=game, org=org))
    return org


async def get_org_by_id(id_: int, dao: OrgByIdGetter) -> dto.SecondaryOrganizer:
    return await dao.get_by_id(id_)
