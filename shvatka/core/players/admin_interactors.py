"""Interactors backing the admin panel player operations.

Each interactor receives the configured superusers via DI and the acting user
via an ``IdentityProvider`` argument, and verifies superuser rights itself
before performing the operation on an arbitrary player.
"""

from dataclasses import dataclass

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.players.adapters import AdminEmailSetter, AdminTgChanger
from shvatka.core.players.superuser import Superusers, check_is_superuser
from shvatka.core.utils import exceptions
from shvatka.core.utils.input_validation import validate_email


@dataclass
class AdminSetPlayerEmailInteractor:
    dao: AdminEmailSetter
    superusers: Superusers

    async def __call__(
        self, identity: IdentityProvider, player_id: int, email: str, is_verified: bool
    ) -> dto.EmailAccount:
        await check_is_superuser(identity, self.superusers)
        player = await self.dao.get_by_id(player_id)
        normalized = validate_email(email)
        if normalized is None:
            raise exceptions.EmailInvalid(text=f"invalid email {email}")
        existing = await self.dao.get_by_email(normalized)
        if existing is not None and existing.player_id != player.id:
            raise exceptions.EmailAlreadyExist(text=f"email {normalized} already occupied")
        account = await self.dao.set_player_email(
            player_id=player.id, email=normalized, is_verified=is_verified
        )
        await self.dao.commit()
        return account


@dataclass
class AdminChangePlayerTgInteractor:
    dao: AdminTgChanger
    superusers: Superusers

    async def __call__(
        self, identity: IdentityProvider, player_id: int, user: dto.User
    ) -> dto.Player:
        await check_is_superuser(identity, self.superusers)
        player = await self.dao.get_by_id(player_id)
        saved = await self.dao.upsert_user(user)
        try:
            already_linked = await self.dao.get_by_user_id(saved.tg_id)
        except exceptions.PlayerNotFoundError:
            already_linked = None
        if already_linked is not None and already_linked.id != player.id:
            raise exceptions.PlayerTgAlreadyLinked(
                player=player,
                text=f"tg {saved.tg_id} already linked to player {already_linked.id}",
            )
        await self.dao.unlink_user(player)
        await self.dao.link_user(player, saved)
        await self.dao.commit()
        return await self.dao.get_by_id(player.id)
