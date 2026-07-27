import typing
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

from shvatka.core.notifications.dto import Notification as NotificationDto
from shvatka.core.notifications.dto import Page as PageDto


@dataclass(kw_only=True, frozen=True, slots=True)
class Notification:
    id: int
    type: str
    severity: str
    payload: Mapping[str, typing.Any]
    created_at: datetime
    read: bool
    actor_id: int | None
    request_id: int | None

    @classmethod
    def from_core(cls, core: NotificationDto) -> "Notification":
        return cls(
            id=core.id,
            type=core.type.name,
            severity=core.severity.name,
            payload=core.payload,
            created_at=core.created_at,
            read=core.is_read,
            actor_id=core.actor_id,
            request_id=core.request_id,
        )


@dataclass(kw_only=True, frozen=True, slots=True)
class NotificationsPage:
    items: Sequence[Notification]
    limit: int
    offset: int
    unread_only: bool

    @classmethod
    def from_core(cls, page: "PageDto[NotificationDto]") -> "NotificationsPage":
        return cls(
            items=[Notification.from_core(n) for n in page.items],
            limit=page.limit,
            offset=page.offset,
            unread_only=bool(page.filters.get("unread_only", False)),
        )


@dataclass(kw_only=True, frozen=True, slots=True)
class UnreadCount:
    count: int
