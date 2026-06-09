from datetime import datetime, tzinfo
import typing
from collections.abc import Collection, Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.models import PushSubscription
from .base import BaseDAO


class PushSubscriptionDAO(BaseDAO[PushSubscription]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(PushSubscription, session, clock=clock)

    async def upsert(
        self,
        *,
        player_id: int,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: str | None,
    ) -> PushSubscription:
        kwargs = {
            "player_id": player_id,
            "endpoint": endpoint,
            "p256dh": p256dh,
            "auth": auth,
            "user_agent": user_agent,
            "enabled": True,
        }
        result = await self.session.execute(
            insert(PushSubscription)
            .values(**kwargs)
            .on_conflict_do_update(
                index_elements=(PushSubscription.endpoint,),
                set_={
                    "player_id": player_id,
                    "p256dh": p256dh,
                    "auth": auth,
                    "user_agent": user_agent,
                    "enabled": True,
                    "updated_at": self.clock(tz_utc),
                },
            )
            .returning(PushSubscription)
        )
        return result.scalar_one()

    async def delete_by_endpoint(self, *, player_id: int, endpoint: str) -> None:
        await self.session.execute(
            delete(PushSubscription).where(
                PushSubscription.player_id == player_id,
                PushSubscription.endpoint == endpoint,
            )
        )

    async def disable_by_endpoint(self, endpoint: str) -> None:
        await self.session.execute(
            update(PushSubscription)
            .where(PushSubscription.endpoint == endpoint)
            .values(enabled=False, updated_at=self.clock(tz_utc))
        )

    async def get_enabled_for_players(
        self, player_ids: Collection[int]
    ) -> Sequence[PushSubscription]:
        if not player_ids:
            return []
        result = await self.session.scalars(
            select(PushSubscription).where(
                PushSubscription.player_id.in_(player_ids),
                PushSubscription.enabled.is_(True),
            )
        )
        return result.all()
