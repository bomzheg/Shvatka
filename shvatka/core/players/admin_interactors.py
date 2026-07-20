"""Interactors backing the admin panel player operations.

Each interactor takes the acting user via an ``IdentityProvider`` argument and
authorises through ``identity.get_superuser()`` before performing the operation
on an arbitrary player.
"""

import logging
from dataclasses import dataclass

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.players.dto import PlayerIdentitiesInfo, TimelineItem, WaiverPoint
from shvatka.core.players.interfaces import (
    PlayerSearcher,
    AdminPlayerReader,
    AdminEmailSetter,
    AdminTgChanger,
    AdminPlayerMerger,
    AdminPlayerWaiverPointsReader,
)
from shvatka.core.players.player import merge_players, get_waiver_points
from shvatka.core.utils import exceptions
from shvatka.core.utils.input_validation import validate_email
from shvatka.core.views.game import GameLogWriter

logger = logging.getLogger(__name__)


@dataclass
class AdminSearchPlayersInteractor:
    dao: PlayerSearcher

    async def __call__(
        self,
        identity: IdentityProvider,
        *,
        username: str | None = None,
        name: str | None = None,
        active: bool = True,
        archive: bool = False,
        can_be_author: bool | None = None,
    ) -> list[dto.Player]:
        admin = await identity.get_superuser()
        logger.warning(
            "admin %s searched players (username=%s, name=%s, can_be_author=%s)",
            admin.id,
            username,
            name,
            can_be_author,
        )
        return await self.dao.search_players(
            username=username,
            name=name,
            active=active,
            archive=archive,
            can_be_author=can_be_author,
        )


@dataclass
class AdminGetPlayerInteractor:
    dao: AdminPlayerReader

    async def __call__(self, identity: IdentityProvider, player_id: int) -> PlayerIdentitiesInfo:
        admin = await identity.get_superuser()
        logger.warning("admin %s viewed player %s", admin.id, player_id)
        player = await self.dao.get_by_id(player_id)
        email = await self.dao.get_email_by_player_id(player.id)
        return PlayerIdentitiesInfo(player=player, email=email)


@dataclass
class AdminSetPlayerEmailInteractor:
    dao: AdminEmailSetter

    async def __call__(
        self, identity: IdentityProvider, player_id: int, email: str, is_verified: bool
    ) -> dto.EmailAccount:
        admin = await identity.get_superuser()
        logger.warning(
            "admin %s changed email of player %s (verified=%s)", admin.id, player_id, is_verified
        )
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

    async def __call__(
        self, identity: IdentityProvider, player_id: int, user: dto.User
    ) -> PlayerIdentitiesInfo:
        admin = await identity.get_superuser()
        logger.warning(
            "admin %s changed tg of player %s to tg_id %s", admin.id, player_id, user.tg_id
        )
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
        updated = await self.dao.get_by_id(player.id)
        email = await self.dao.get_email_by_player_id(updated.id)
        return PlayerIdentitiesInfo(player=updated, email=email)


@dataclass
class AdminGetPlayerWaiverPointsInteractor:
    dao: AdminPlayerWaiverPointsReader

    async def __call__(self, identity: IdentityProvider, player_id: int) -> list[WaiverPoint]:
        """List intervals in which the player's team membership is fixed by waivers."""
        admin = await identity.get_superuser()
        logger.warning("admin %s viewed waiver points of player %s", admin.id, player_id)
        return await get_waiver_points(await self.dao.get_by_id(player_id), self.dao)


@dataclass
class AdminMergePlayersInteractor:
    dao: AdminPlayerMerger
    game_log: GameLogWriter

    async def __call__(
        self,
        identity: IdentityProvider,
        primary_id: int,
        secondary_id: int,
        timeline: list[TimelineItem] | None = None,
    ) -> dto.Player:
        """Merge ``secondary`` player into ``primary``; ``secondary`` is deleted.

        When the players' team histories are not compatible, the admin can pass a
        manually built ``timeline`` which replaces both histories; it is validated
        against the waiver points of both players.
        """
        admin = await identity.get_superuser()
        logger.warning("admin %s merges player %s into %s", admin.id, secondary_id, primary_id)
        if primary_id == secondary_id:
            raise exceptions.MergeError(
                player_id=primary_id, notify_user="нельзя объединить игрока с самим собой"
            )
        primary = await self.dao.get_by_id(primary_id)
        secondary = await self.dao.get_by_id(secondary_id)
        await merge_players(primary, secondary, self.game_log, self.dao, timeline=timeline)
        return await self.dao.get_by_id(primary_id)
