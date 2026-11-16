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
from shvatka.core.season.rules import SLOT_SUGGEST_WINDOW
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
    """A re-planned game drags its date along — but only a short distance.

    `PlanGameStartInteractor` applies this after a successful re-plan. It is a
    service rather than an interactor precisely so that interactor can depend
    on it: the schedule follows the game, never the other way round.

    Within `SLOT_SUGGEST_WINDOW` the date follows the game: a small correction
    of the start is the same evening replanned. Beyond it the game leaves the
    date instead — a season is one year, and a date dragged past the New Year
    line would sit in a year the season cannot honestly show.
    """

    dao: SeasonScheduleDao
    changes: ScheduleChangeLog

    async def __call__(self, game: dto.Game, actor: dto.Player) -> bool:
        """Returns whether the game sits in a date — what «вне расписания» reads."""
        slot = await self.dao.get_slot_by_game(game.id)
        if slot is None:
            return False
        if game.start_at is None:
            return True
        started = game.start_at.astimezone(tz_game).date()
        if started == slot.slot_date:
            return True
        season = await self.dao.get_season_by_id(slot.season_id)
        if season is None:
            return True
        if abs((started - slot.slot_date).days) > SLOT_SUGGEST_WINDOW.days:
            await self._unlink(slot, season, game, actor=actor)
            return False
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
        return True

    async def _unlink(
        self,
        slot: season_dto.Slot,
        season: season_dto.Season,
        game: dto.Game,
        *,
        actor: dto.Player,
    ) -> None:
        await self.dao.unlink_game(slot.id)
        await self.changes.record(
            season,
            season_dto.ChangeType.slot_game_unlinked,
            slot_id=slot.id,
            actor=actor,
            payload={
                "date": slot.slot_date.isoformat(),
                "game": game.name,
                "game_id": game.id,
                "reason": "game_rescheduled_far",
            },
        )
        await self.dao.commit()
        await self.changes.announce_update(season.year)
