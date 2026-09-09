from __future__ import annotations

from typing import Protocol

from shvatka.core.interfaces.dal.season import (
    ScheduleChangeReader,
    ScheduleChangeWriter,
    SeasonAudienceReader,
    SeasonReader,
    SeasonWriter,
    SlotOrgWriter,
    SlotReader,
    SlotWriter,
)
from shvatka.core.models import dto
from shvatka.core.notifications.adapters import NotificationWriter


class SeasonScheduleDao(
    SeasonReader,
    SeasonWriter,
    SlotReader,
    SlotWriter,
    SlotOrgWriter,
    ScheduleChangeReader,
    ScheduleChangeWriter,
    SeasonAudienceReader,
    NotificationWriter,
    Protocol,
):
    """Everything a season use case may need, behind one Protocol.

    `AGENTS.md` allows an interactor at most one dao, so the four season tables
    and the notification feed are composed here and implemented once in
    `infrastructure/db/dao/complex/season.py`.
    """

    async def get_player_by_id(self, id_: int) -> dto.Player:
        raise NotImplementedError

    async def get_team_by_id(self, id_: int) -> dto.Team:
        raise NotImplementedError

    async def get_game_by_id(self, id_: int) -> dto.Game:
        raise NotImplementedError
