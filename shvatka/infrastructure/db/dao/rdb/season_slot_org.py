import typing
from collections.abc import Collection
from datetime import datetime, tzinfo

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.infrastructure.db.models import SeasonSlotOrg

from .base import BaseDAO


class SeasonSlotOrgDao(BaseDAO[SeasonSlotOrg]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(SeasonSlotOrg, session, clock=clock)

    async def set_slot_orgs(self, slot_id: int, player_ids: Collection[int]) -> None:
        await self.session.execute(delete(SeasonSlotOrg).where(SeasonSlotOrg.slot_id == slot_id))
        for player_id in dict.fromkeys(player_ids):
            self._save(SeasonSlotOrg(slot_id=slot_id, player_id=player_id))
        await self.session.flush()
