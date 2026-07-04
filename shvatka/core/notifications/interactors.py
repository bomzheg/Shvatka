"""Interactors backing the web "notifications" tab: read the feed and mark read."""

from collections.abc import Collection, Sequence
from dataclasses import dataclass

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.notifications import dto
from shvatka.core.notifications.adapters import NotificationReader, NotificationMarker


@dataclass
class ListNotificationsInteractor:
    dao: NotificationReader

    async def __call__(
        self,
        identity: IdentityProvider,
        *,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[dto.Notification]:
        player = await identity.get_required_player()
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        return await self.dao.get_for_player(
            player.id, unread_only=unread_only, limit=limit, offset=offset
        )


@dataclass
class UnreadCountInteractor:
    dao: NotificationReader

    async def __call__(self, identity: IdentityProvider) -> int:
        player = await identity.get_required_player()
        return await self.dao.count_unread(player.id)


@dataclass
class MarkNotificationsReadInteractor:
    dao: NotificationMarker

    async def __call__(
        self, identity: IdentityProvider, notification_ids: Collection[int]
    ) -> None:
        player = await identity.get_required_player()
        await self.dao.mark_read(player.id, notification_ids)
        await self.dao.commit()


@dataclass
class MarkAllNotificationsReadInteractor:
    dao: NotificationMarker

    async def __call__(self, identity: IdentityProvider) -> None:
        player = await identity.get_required_player()
        await self.dao.mark_all_read(player.id)
        await self.dao.commit()
