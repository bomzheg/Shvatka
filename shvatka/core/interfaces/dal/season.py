from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import date, datetime
from typing import Any, Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.season import dto


class SeasonReader(Protocol):
    async def get_season(self, year: int) -> dto.Season | None:
        raise NotImplementedError

    async def get_season_by_id(self, season_id: int) -> dto.Season | None:
        raise NotImplementedError

    async def get_season_years(self) -> Sequence[int]:
        raise NotImplementedError

    async def get_seasons_to_close(self, today: date) -> Sequence[dto.Season]:
        raise NotImplementedError


class SeasonWriter(Committer, Protocol):
    async def create_season(self, year: int, published_by_id: int) -> dto.Season:
        raise NotImplementedError

    async def set_announcement(self, season_id: int, *, chat_id: int, message_id: int) -> None:
        raise NotImplementedError

    async def set_unpinned(self, season_id: int) -> None:
        raise NotImplementedError

    async def touch_season(self, season_id: int) -> None:
        raise NotImplementedError


class SlotReader(Protocol):
    async def get_slot(self, slot_id: int) -> dto.Slot:
        raise NotImplementedError

    async def get_slot_by_game(self, game_id: int) -> dto.Slot | None:
        raise NotImplementedError

    async def lock_slot(self, slot_id: int) -> dto.Slot:
        """Re-read the row `FOR UPDATE`, so two takers cannot both win."""
        raise NotImplementedError


class SlotWriter(Committer, Protocol):
    async def add_slot(self, season_id: int, day: date, note: str | None = ...) -> dto.Slot:
        raise NotImplementedError

    async def move_slot(self, slot_id: int, day: date) -> None:
        raise NotImplementedError

    async def set_slot_note(self, slot_id: int, note: str | None) -> None:
        raise NotImplementedError

    async def remove_slot(self, slot_id: int) -> None:
        raise NotImplementedError

    async def take_slot(
        self,
        slot_id: int,
        *,
        owner_id: int,
        author_kind: dto.SlotAuthorKind,
        team_id: int | None = ...,
    ) -> None:
        raise NotImplementedError

    async def release_slot(self, slot_id: int) -> None:
        raise NotImplementedError

    async def link_game(self, slot_id: int, game_id: int) -> None:
        raise NotImplementedError

    async def unlink_game(self, slot_id: int) -> None:
        raise NotImplementedError


class SlotOrgWriter(Committer, Protocol):
    async def set_slot_orgs(self, slot_id: int, player_ids: Collection[int]) -> None:
        raise NotImplementedError


class ScheduleChangeWriter(Committer, Protocol):
    async def add_change(
        self,
        *,
        season_id: int,
        type_: dto.ChangeType,
        slot_id: int | None = ...,
        actor_id: int | None = ...,
        payload: dict[str, Any] | None = ...,
    ) -> dto.ScheduleChange:
        raise NotImplementedError

    async def mark_changes_published(self, change_ids: Collection[int]) -> None:
        raise NotImplementedError


class ScheduleChangeReader(Protocol):
    async def get_unpublished_changes(self, season_id: int) -> Sequence[dto.ScheduleChange]:
        raise NotImplementedError

    async def get_season_ids_with_unpublished_changes(self) -> Sequence[int]:
        raise NotImplementedError


class SeasonAudienceReader(Protocol):
    async def get_recipient_ids(self, since: datetime) -> set[int]:
        """Everyone who played or organized in the window, in a team or not."""
        raise NotImplementedError
