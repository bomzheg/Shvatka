from shvatka.dal.organizer import GameOrgsGetter, OrgAdder, OrgByIdGetter, OrgPermissionFlipper, OrgDeletedFlipper, \
    OrgByPlayerGetter
from shvatka.dal.secure_invite import InviteSaver, InviteRemover
from shvatka.models import dto, enums
from shvatka.models.enums.invite_type import InviteType
from shvatka.models.enums.org_permission import OrgPermission
from shvatka.services.game import get_game
from shvatka.utils.exceptions import PermissionsError, GameHasAnotherAuthor, SaltError
from shvatka.views.game import OrgNotifier, NewOrg


async def get_orgs(game: dto.Game, dao: GameOrgsGetter) -> list[dto.Organizer]:
    return [*await get_primary_orgs(game), *await dao.get_orgs(game)]


async def get_spying_orgs(game: dto.Game, dao: GameOrgsGetter) -> list[dto.Organizer]:
    return [org for org in await get_orgs(game, dao) if org.can_spy]


async def get_primary_orgs(game: dto.Game) -> list[dto.PrimaryOrganizer]:
    return [dto.PrimaryOrganizer(player=game.author, game=game)]


async def get_secondary_orgs(
    game: dto.Game, dao: GameOrgsGetter, with_deleted: bool = False,
) -> list[dto.SecondaryOrganizer]:
    return await dao.get_orgs(game, with_deleted=with_deleted)


def check_allow_manage_orgs(game: dto.Game, manager_id: int):
    if game.author.id != manager_id:
        raise GameHasAnotherAuthor(game=game, player_id=manager_id, alarm=True)


def check_game_token(game: dto.Game, manage_token: str):
    if game.manage_token != manage_token:
        raise PermissionsError(permission_name="add_game_organizer", game=game)


async def save_invite_to_orgs(game: dto.Game, inviter: dto.Player, dao: InviteSaver) -> str:
    return await dao.save_new_invite(dct=dict(
        game_id=game.id, inviter_id=inviter.id, type_=InviteType.add_org.name,
    ))


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
    if data["type_"] != InviteType.add_org.name:
        raise SaltError(text="Ошибка нарушения данных. Тип в зашифрованной и открытой части не совпал", alarm=True)
    if data["inviter_id"] != inviter_id:
        raise SaltError(text="Ошибка нарушения данных. Токен в зашифрованной и открытой части не совпал", alarm=True)
    game = await get_game(id_=data["game_id"], dao=dao)
    check_allow_manage_orgs(game, inviter_id)
    notify_orgs = await get_orgs(game, dao)
    org = await dao.add_new_org(game, player)
    await dao.commit()
    await org_notifier.notify(NewOrg(orgs_list=notify_orgs, game=game, org=org))
    return org


async def get_org_by_id(id_: int, dao: OrgByIdGetter) -> dto.SecondaryOrganizer:
    return await dao.get_by_id(id_)


async def get_by_player_or_none(player: dto.Player, game: dto.Game, dao: OrgByPlayerGetter) -> dto.Organizer | None:
    if game.author.id == player.id:
        return dto.PrimaryOrganizer(player=player, game=game)
    return await dao.get_by_player_or_none(player=player, game=game)


async def get_by_player(player: dto.Player, game: dto.Game, dao: OrgByPlayerGetter) -> dto.Organizer:
    if game.author.id == player.id:
        return dto.PrimaryOrganizer(player=player, game=game)
    return await dao.get_by_player(player=player, game=game)


async def flip_permission(
    manager: dto.Player, org: dto.SecondaryOrganizer, permission: OrgPermission, dao: OrgPermissionFlipper,
):
    check_allow_manage_orgs(org.game, manager.id)
    await dao.flip_permission(org, permission)
    await dao.commit()


async def flip_deleted(manager: dto.Player, org: dto.SecondaryOrganizer, dao: OrgDeletedFlipper):
    check_allow_manage_orgs(org.game, manager.id)
    await dao.flip_deleted(org)
    await dao.commit()


def check_can_see_log_keys(org: dto.Organizer):
    if not org.can_see_log_keys:
        raise PermissionsError(
            permission_name=enums.OrgPermission.can_see_log_keys.name,
            player=org.player,
            game=org.game,
        )


def check_can_spy(org: dto.Organizer):
    if not org.can_spy:
        raise PermissionsError(
            permission_name=enums.OrgPermission.can_spy.name,
            player=org.player,
            game=org.game,
        )
