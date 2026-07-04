"""Interactors backing the admin panel player operations.

They are authorised at the transport edge (only superusers may reach them), so
they do not re-check permissions themselves — they just perform the operation on
behalf of an admin acting on an arbitrary player.
"""

from dataclasses import dataclass

from shvatka.core.models import dto
from shvatka.core.players.adapters import AdminEmailSetter, AdminTgChanger
from shvatka.core.utils import exceptions
from shvatka.core.utils.input_validation import validate_email


@dataclass
class AdminSetPlayerEmailInteractor:
    dao: AdminEmailSetter

    async def __call__(self, player_id: int, email: str, is_verified: bool) -> dto.EmailAccount:
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

    async def __call__(self, player_id: int, user: dto.User) -> dto.Player:
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
