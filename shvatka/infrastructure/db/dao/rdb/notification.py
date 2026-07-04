import typing
from collections.abc import Collection, Sequence
from datetime import datetime, tzinfo
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.models.enums.notification import NotificationType, NotificationSeverity
from shvatka.core.notifications import dto
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.models import Notification
from .base import BaseDAO


class NotificationDAO(BaseDAO[Notification]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(Notification, session, clock=clock)

    async def create(
        self,
        *,
        recipient_id: int,
        type_: NotificationType,
        severity: NotificationSeverity = NotificationSeverity.normal,
        actor_id: int | None = None,
        payload: dict[str, Any] | None = None,
        request_id: int | None = None,
    ) -> dto.Notification:
        notification = Notification(
            recipient_id=recipient_id,
            type=type_.name,
            severity=severity,
            actor_id=actor_id,
            payload=payload or {},
            request_id=request_id,
        )
        self._save(notification)
        await self._flush(notification)
        return notification.to_dto()

    async def create_for_recipients(
        self,
        *,
        recipient_ids: Collection[int],
        type_: NotificationType,
        severity: NotificationSeverity = NotificationSeverity.normal,
        actor_id: int | None = None,
        payload: dict[str, Any] | None = None,
        request_id: int | None = None,
    ) -> None:
        for recipient_id in set(recipient_ids):
            self._save(
                Notification(
                    recipient_id=recipient_id,
                    type=type_.name,
                    severity=severity,
                    actor_id=actor_id,
                    payload=payload or {},
                    request_id=request_id,
                )
            )

    async def get_for_player(
        self,
        player_id: int,
        *,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[dto.Notification]:
        stmt = select(Notification).where(Notification.recipient_id == player_id)
        if unread_only:
            stmt = stmt.where(Notification.read_at.is_(None))
        stmt = stmt.order_by(Notification.created_at.desc(), Notification.id.desc())
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.scalars(stmt)
        return [notification.to_dto() for notification in result.all()]

    async def count_unread(self, player_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Notification.id)).where(
                Notification.recipient_id == player_id,
                Notification.read_at.is_(None),
            )
        )
        return result.scalar_one()

    async def mark_read(self, player_id: int, notification_ids: Collection[int]) -> None:
        if not notification_ids:
            return
        await self.session.execute(
            update(Notification)
            .where(
                Notification.recipient_id == player_id,
                Notification.id.in_(notification_ids),
                Notification.read_at.is_(None),
            )
            .values(read_at=self.clock(tz_utc))
        )

    async def mark_all_read(self, player_id: int) -> None:
        await self.session.execute(
            update(Notification)
            .where(
                Notification.recipient_id == player_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=self.clock(tz_utc))
        )
