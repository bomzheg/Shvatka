import pytest

from shvatka.core.models import dto
from shvatka.core.models.enums import InviteType
from shvatka.core.models.enums import OrgPermission
from shvatka.core.services.organizers import (
    get_orgs,
    get_spying_orgs,
    get_secondary_orgs,
    check_allow_manage_orgs,
    check_game_token,
    save_invite_to_orgs,
    dismiss_to_be_org,
    agree_to_be_org,
    flip_permission,
    flip_deleted,
)
from shvatka.core.utils.exceptions import SaltNotExist
from shvatka.core.views.game import NewOrg
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.mocks.org_notifier import OrgNotifierMock


@pytest.mark.asyncio
async def test_only_org(game: dto.FullGame, author: dto.Player, dao: HolderDao):
    orgs = await get_orgs(game, dao.organizer)
    assert 1 == len(orgs)
    assert author.id == orgs[0].player.id

    orgs = await get_spying_orgs(game, dao.organizer)
    assert 1 == len(orgs)
    assert author.id == orgs[0].player.id

    assert [] == await get_secondary_orgs(game, dao.organizer)

    check_allow_manage_orgs(game, author.id)
    check_game_token(game, game.manage_token)


@pytest.mark.asyncio
async def test_dismiss_invite(game: dto.FullGame, author: dto.Player, dao: HolderDao):
    token = await save_invite_to_orgs(game, author, dao.secure_invite)
    expected = {"game_id": game.id, "inviter_id": author.id, "type_": InviteType.add_org.name}
    assert expected == await dao.secure_invite.get_invite(token)
    await dismiss_to_be_org(token, dao.secure_invite)
    with pytest.raises(SaltNotExist):
        await dao.secure_invite.get_invite(token)


@pytest.mark.asyncio
async def test_agree_invite(
    game: dto.FullGame, author: dto.Player, harry: dto.Player, dao: HolderDao, check_dao: HolderDao
):
    token = await save_invite_to_orgs(game, author, dao.secure_invite)
    org_notifier = OrgNotifierMock()
    await agree_to_be_org(
        token=token,
        inviter_id=author.id,
        player=harry,
        org_notifier=org_notifier,
        dao=dao.org_adder,
    )
    secondary_orgs = await get_secondary_orgs(game, check_dao.organizer)
    assert 1 == len(secondary_orgs)
    actual = secondary_orgs[0]

    assert game.id == actual.game.id
    assert harry.id == actual.player.id
    assert not actual.can_spy
    assert not actual.can_see_log_keys
    assert not actual.can_validate_waivers
    assert not actual.deleted

    event = org_notifier.calls.pop()
    assert not org_notifier.calls
    assert isinstance(event, NewOrg)
    assert game.id == event.game.id
    assert actual.id == event.org.id
    assert harry.id == event.org.player.id
    assert 1 == len(event.orgs_list)
    assert author.id == event.orgs_list[0].player.id


@pytest.mark.parametrize("permission", list(OrgPermission))
@pytest.mark.asyncio
async def test_flip_permission(
    game: dto.FullGame,
    author: dto.Player,
    harry: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
    permission: OrgPermission,
):
    org = await dao.organizer.add_new(game, harry)
    await dao.commit()
    assert not getattr(org, permission.name)

    await flip_permission(author, org, permission, dao.organizer)
    org = await check_dao.organizer.get_by_id(org.id)
    assert getattr(org, permission.name)

    await flip_permission(author, org, permission, dao.organizer)
    org = await check_dao.organizer.get_by_id(org.id)
    assert not getattr(org, permission.name)


@pytest.mark.asyncio
async def test_flip_deleted(
    game: dto.FullGame,
    author: dto.Player,
    harry: dto.Player,
    dao: HolderDao,
    check_dao: HolderDao,
):
    org = await dao.organizer.add_new(game, harry)
    await dao.commit()
    assert not org.deleted

    await flip_deleted(author, org, dao.organizer)
    org = await check_dao.organizer.get_by_id(org.id)
    assert org.deleted

    await flip_deleted(author, org, dao.organizer)
    org = await check_dao.organizer.get_by_id(org.id)
    assert not org.deleted
