"""Interactors used by the web UI / API to manage organizers of a game.

They wrap the domain services from :mod:`shvatka.core.services.organizers` so the
transport layer (api routes) stays thin and the access rules live in one place.
"""

import logging
from dataclasses import dataclass

from shvatka.core.interfaces.dal.game import GameByIdGetter
from shvatka.core.interfaces.dal.organizer import (
    GameOrgsGetter,
    OrgAdder,
    OrgByPlayerGetter,
    OrgDeletedFlipper,
    OrgPermissionFlipper,
)
from shvatka.core.interfaces.dal.player import PlayerByIdGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums.org_permission import OrgPermission
from shvatka.core.services.game import get_game
from shvatka.core.services.organizers import (
    check_allow_manage_orgs,
    flip_deleted,
    flip_permission,
    get_org_by_id,
    get_primary_orgs,
    get_secondary_orgs,
)
from shvatka.core.utils import exceptions

logger = logging.getLogger(__name__)


@dataclass
class ListGameOrgsInteractor:
    game_dao: GameByIdGetter
    org_dao: GameOrgsGetter

    async def __call__(self, game_id: int, identity: IdentityProvider) -> list[dto.Organizer]:
        game = await get_game(id_=game_id, dao=self.game_dao)
        await check_can_view_orgs(game, identity)
        primary = await get_primary_orgs(game)
        secondary = await get_secondary_orgs(game, self.org_dao, with_deleted=True)
        return [*primary, *secondary]


@dataclass
class AddGameOrgInteractor:
    game_dao: GameByIdGetter
    player_dao: PlayerByIdGetter
    org_getter: OrgByPlayerGetter
    org_adder: OrgAdder
    org_deleted_flipper: OrgDeletedFlipper

    async def __call__(
        self, game_id: int, player_id: int, identity: IdentityProvider
    ) -> dto.SecondaryOrganizer:
        manager = await identity.get_required_player()
        game = await get_game(id_=game_id, dao=self.game_dao)
        check_allow_manage_orgs(game, manager.id)
        player = await self.player_dao.get_by_id(player_id)
        existing = await self.org_getter.get_by_player_or_none(game=game, player=player)
        if existing is not None:
            if not existing.deleted:
                raise exceptions.PlayerAlreadyOrganizer(
                    player=player,
                    game=game,
                    text="player is already an organizer of this game",
                )
            # a previously removed organizer is restored via the same POST endpoint
            await flip_deleted(manager, existing, self.org_deleted_flipper)
            return await self.org_deleted_flipper.get_by_id(existing.id)
        org = await self.org_adder.add_new_org(game, player)
        await self.org_adder.commit()
        return org


@dataclass
class ChangeOrgPermissionInteractor:
    game_dao: GameByIdGetter
    org_dao: OrgPermissionFlipper

    async def __call__(
        self,
        game_id: int,
        org_id: int,
        permission: OrgPermission,
        value: bool,
        identity: IdentityProvider,
    ) -> dto.SecondaryOrganizer:
        manager = await identity.get_required_player()
        game = await get_game(id_=game_id, dao=self.game_dao)
        check_allow_manage_orgs(game, manager.id)
        org = await get_org_by_id(org_id, self.org_dao)
        check_org_belongs_to_game(org, game.id)
        if getattr(org, permission.name) != value:
            await flip_permission(manager, org, permission, self.org_dao)
        return await self.org_dao.get_by_id(org_id)


@dataclass
class RemoveGameOrgInteractor:
    game_dao: GameByIdGetter
    org_dao: OrgDeletedFlipper

    async def __call__(
        self, game_id: int, org_id: int, identity: IdentityProvider
    ) -> dto.SecondaryOrganizer:
        manager = await identity.get_required_player()
        game = await get_game(id_=game_id, dao=self.game_dao)
        check_allow_manage_orgs(game, manager.id)
        org = await get_org_by_id(org_id, self.org_dao)
        check_org_belongs_to_game(org, game.id)
        if not org.deleted:
            await flip_deleted(manager, org, self.org_dao)
        return await self.org_dao.get_by_id(org_id)


async def check_can_view_orgs(game: dto.Game, identity: IdentityProvider) -> None:
    """Completed games are public; for the rest only the author and orgs may look."""
    if game.is_complete():
        return
    org = await identity.get_org(game)
    if org is None:
        raise exceptions.IsNotOrganizer(
            player=await identity.get_player(),
            game_id=game.id,
        )


def check_org_belongs_to_game(org: dto.SecondaryOrganizer, game_id: int) -> None:
    if org.game.id != game_id:
        raise exceptions.GameNotFound(
            game_id=game_id,
            text=f"organizer {org.id} does not belong to game {game_id}",
        )
