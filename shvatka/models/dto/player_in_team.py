from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


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
