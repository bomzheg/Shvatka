from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EmailAccount:
    email: str
    player_id: int
    db_id: int
    is_verified: bool = False


@dataclass
class EmailConfirmation:
    email: str
    code: str
    player_id: int
