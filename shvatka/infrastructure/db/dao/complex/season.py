from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy import select, union

from shvatka.core.models import dto
from shvatka.core.models.enums.notification import NotificationSeverity, NotificationType
from shvatka.core.notifications import dto as notification_dto
from shvatka.core.notifications.adapters import NotificationWriter
from shvatka.core.season import dto as season_dto
from shvatka.core.season.adapters import SeasonScheduleDao
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.db.models import Game, Organizer, TeamPlayer


@dataclass
class SeasonScheduleDaoImpl(SeasonScheduleDao):
    """The four season tables and the notification feed behind one Protocol.

    Every write still belongs to its own table's dao — this only puts them in
    one place, so a season interactor takes a single dao. The ordering is the
    interactor's, not this class's.
    """

    dao: HolderDao
    notifications: NotificationWriter

    async def commit(self) -> None:
        await self.dao.commit()

    async def get_season(self, year: int) -> season_dto.Season | None:
        return await self.dao.season.get_season(year)

    async def get_season_by_id(self, season_id: int) -> season_dto.Season | None:
        return await self.dao.season.get_season_by_id(season_id)

    async def get_season_years(self) -> Sequence[int]:
        return await self.dao.season.get_season_years()

    async def get_seasons_to_close(self, today: date) -> Sequence[season_dto.Season]:
        return await self.dao.season.get_seasons_to_close(today)

    async def create_season(self, year: int, published_by_id: int) -> season_dto.Season:
        return await self.dao.season.create_season(year, published_by_id=published_by_id)

    async def set_announcement(self, season_id: int, *, chat_id: int, message_id: int) -> None:
        await self.dao.season.set_announcement(season_id, chat_id=chat_id, message_id=message_id)

    async def set_unpinned(self, season_id: int) -> None:
        await self.dao.season.set_unpinned(season_id)

    async def touch_season(self, season_id: int) -> None:
        await self.dao.season.touch_season(season_id)

    async def get_slot(self, slot_id: int) -> season_dto.Slot:
        return await self.dao.season_slot.get_slot(slot_id)

    async def get_slot_by_game(self, game_id: int) -> season_dto.Slot | None:
        return await self.dao.season_slot.get_slot_by_game(game_id)

    async def lock_slot(self, slot_id: int) -> season_dto.Slot:
        return await self.dao.season_slot.lock_slot(slot_id)

    async def add_slot(
        self, season_id: int, day: date, note: str | None = None
    ) -> season_dto.Slot:
        return await self.dao.season_slot.add_slot(season_id, day, note)

    async def move_slot(self, slot_id: int, day: date) -> None:
        await self.dao.season_slot.move_slot(slot_id, day)

    async def set_slot_note(self, slot_id: int, note: str | None) -> None:
        await self.dao.season_slot.set_slot_note(slot_id, note)

    async def remove_slot(self, slot_id: int) -> None:
        await self.dao.season_slot.remove_slot(slot_id)

    async def take_slot(
        self,
        slot_id: int,
        *,
        owner_id: int,
        author_kind: season_dto.SlotAuthorKind,
        team_id: int | None = None,
    ) -> None:
        await self.dao.season_slot.take_slot(
            slot_id, owner_id=owner_id, author_kind=author_kind, team_id=team_id
        )

    async def release_slot(self, slot_id: int) -> None:
        await self.dao.season_slot.release_slot(slot_id)

    async def link_game(self, slot_id: int, game_id: int) -> None:
        await self.dao.season_slot.link_game(slot_id, game_id)

    async def unlink_game(self, slot_id: int) -> None:
        await self.dao.season_slot.unlink_game(slot_id)

    async def set_slot_orgs(self, slot_id: int, player_ids: Collection[int]) -> None:
        await self.dao.season_slot_org.set_slot_orgs(slot_id, player_ids)

    async def add_change(
        self,
        *,
        season_id: int,
        type_: season_dto.ChangeType,
        slot_id: int | None = None,
        actor_id: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> season_dto.ScheduleChange:
        return await self.dao.season_change.add_change(
            season_id=season_id,
            type_=type_,
            slot_id=slot_id,
            actor_id=actor_id,
            payload=payload,
        )

    async def mark_changes_published(self, change_ids: Collection[int]) -> None:
        await self.dao.season_change.mark_changes_published(change_ids)

    async def get_unpublished_changes(self, season_id: int) -> Sequence[season_dto.ScheduleChange]:
        return await self.dao.season_change.get_unpublished_changes(season_id)

    async def get_season_ids_with_unpublished_changes(self) -> Sequence[int]:
        return await self.dao.season_change.get_season_ids_with_unpublished_changes()

    async def get_player_by_id(self, id_: int) -> dto.Player:
        return await self.dao.player.get_by_id(id_)

    async def get_team_by_id(self, id_: int) -> dto.Team:
        return await self.dao.team.get_by_id(id_)

    async def get_game_by_id(self, id_: int) -> dto.Game:
        return await self.dao.game.get_by_id(id_)

    async def get_recipient_ids(self, since: datetime) -> set[int]:
        """Anyone in a team in the window, plus everyone who organized in it.

        Rooted at no single table, so it lives here rather than on one of the
        per-table daos — one union, run at most once a day per season.
        """
        in_a_team = select(TeamPlayer.player_id).where(
            TeamPlayer.date_left.is_(None) | (TeamPlayer.date_left >= since)
        )
        organized = (
            select(Organizer.player_id)
            .join(Game, Game.id == Organizer.game_id)
            .where(Organizer.deleted.is_(False), Game.start_at >= since)
        )
        authored = select(Game.author_id).where(Game.start_at >= since)
        result = await self.dao.session.scalars(union(in_a_team, organized, authored))
        return set(result.all())

    async def create(
        self,
        *,
        recipient_id: int,
        type_: NotificationType,
        severity: NotificationSeverity = NotificationSeverity.normal,
        actor_id: int | None = None,
        payload: dict[str, Any] | None = None,
        request_id: int | None = None,
    ) -> notification_dto.Notification:
        return await self.notifications.create(
            recipient_id=recipient_id,
            type_=type_,
            severity=severity,
            actor_id=actor_id,
            payload=payload,
            request_id=request_id,
        )

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
        await self.notifications.create_for_recipients(
            recipient_ids=recipient_ids,
            type_=type_,
            severity=severity,
            actor_id=actor_id,
            payload=payload,
            request_id=request_id,
        )
