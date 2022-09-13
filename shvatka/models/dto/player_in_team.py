from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from shvatka.models import db


@dataclass
class PlayerInTeam:
    id: int
    player_id: int
    team_id: int
    date_joined: datetime
    date_left: datetime | None
    role: str
    emoji: str

    can_manage_waivers: bool
    can_manage_players: bool
    can_change_team_name: bool
    can_add_players: bool
    can_remove_players: bool

    @classmethod
    def from_db(cls, pit: db.PlayerInTeam) -> PlayerInTeam:
        return cls(
            id=pit.id,
            player_id=pit.player_id,
            team_id=pit.team_id,
            date_joined=pit.date_joined,
            date_left=pit.date_left,
            role=pit.role,
            emoji=pit.emoji,

            can_manage_waivers=pit.can_manage_waivers,
            can_manage_players=pit.can_manage_players,
            can_change_team_name=pit.can_change_team_name,
            can_add_players=pit.can_add_players,
            can_remove_players=pit.can_remove_players,
        )
