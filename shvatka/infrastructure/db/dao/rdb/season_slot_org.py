import typing
from collections.abc import Collection
from datetime import datetime, tzinfo

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shvatka.infrastructure.db.models import SeasonSlotOrg

from .base import BaseDAO


class SeasonSlotOrgDao(BaseDAO[SeasonSlotOrg]):
    def __init__(
        self, session: AsyncSession, clock: typing.Callable[[tzinfo], datetime] = datetime.now
    ) -> None:
        super().__init__(SeasonSlotOrg, session, clock=clock)

    async def replace_player(self, primary_id: int, secondary_id: int) -> None:
        """Move the org seats of a merged-away player, without seating them twice.

        `(slot_id, player_id)` is unique, so a date that already names the
        surviving player loses the duplicate row rather than colliding: after a
        merge the two of them are one person.
        """
        already = select(SeasonSlotOrg.slot_id).where(SeasonSlotOrg.player_id == primary_id)
        await self.session.execute(
            delete(SeasonSlotOrg).where(
                SeasonSlotOrg.player_id == secondary_id,
                SeasonSlotOrg.slot_id.in_(already),
            )
        )
        await self.session.execute(
            update(SeasonSlotOrg)
            .where(SeasonSlotOrg.player_id == secondary_id)
            .values(player_id=primary_id)
        )

    async def set_slot_orgs(self, slot_id: int, player_ids: Collection[int]) -> None:
        await self.session.execute(delete(SeasonSlotOrg).where(SeasonSlotOrg.slot_id == slot_id))
        for player_id in dict.fromkeys(player_ids):
            self._save(SeasonSlotOrg(slot_id=slot_id, player_id=player_id))
        await self.session.flush()
