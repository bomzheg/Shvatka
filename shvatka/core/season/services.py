"""Season domain services: what a use case leans on, but is not itself.

Neither of these is an interactor. `ScheduleChangeLog` is the bookkeeping every
edit of a published season shares, and `LinkedSlotSync` is a rule another
area's interactor has to apply — an interactor never calls another interactor.
Both are plain classes dishka builds like anything else.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from shvatka.core.models import dto
from shvatka.core.season import dto as season_dto
from shvatka.core.season.adapters import SeasonScheduleDao
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.core.views.season import SeasonAnnouncer

logger = logging.getLogger(__name__)


@dataclass
class ScheduleChangeLog:
    """The trail an edit leaves, and the pinned message it has to refresh."""

    dao: SeasonScheduleDao
    announcer: SeasonAnnouncer

    async def record(
        self,
        season: season_dto.Season,
        type_: season_dto.ChangeType,
        *,
        slot_id: int | None,
        actor: dto.Player,
        payload: dict[str, Any],
    ) -> None:
        """Called before the commit: the audit row shares the write's transaction."""
        await self.dao.add_change(
            season_id=season.id,
            type_=type_,
            slot_id=slot_id,
            actor_id=actor.id,
            payload=payload,
        )
        await self.dao.touch_season(season.id)

    async def announce_update(self, year: int) -> None:
        """Post-commit and best-effort: the pin must show current truth."""
        try:
            season = await self.dao.get_season(year)
            if season is not None:
                await self.announcer.update(season)
        except Exception as e:  # noqa: BLE001
            logger.warning("can't update the schedule message of %s", year, exc_info=e)


@dataclass
class LinkedSlotSync:
    """A re-planned game drags its date along. Cancelling a start unlinks nothing.

    `PlanGameStartInteractor` applies this after a successful re-plan. It is a
    service rather than an interactor precisely so that interactor can depend
    on it: the schedule follows the game, never the other way round.
    """

    dao: SeasonScheduleDao
    changes: ScheduleChangeLog

    async def __call__(self, game: dto.Game, actor: dto.Player) -> None:
        if game.start_at is None:
            return
        slot = await self.dao.get_slot_by_game(game.id)
        if slot is None:
            return
        started = game.start_at.astimezone(tz_game).date()
        if started == slot.slot_date:
            return
        season = await self.dao.get_season_by_id(slot.season_id)
        if season is None:
            return
        previous = slot.slot_date
        await self.dao.move_slot(slot.id, started)
        await self.changes.record(
            season,
            season_dto.ChangeType.slot_moved,
            slot_id=slot.id,
            actor=actor,
            payload={
                "from": previous.isoformat(),
                "to": started.isoformat(),
                "date": started.isoformat(),
                "reason": "game_rescheduled",
            },
        )
        await self.dao.commit()
        await self.changes.announce_update(season.year)
