from __future__ import annotations

from dataclasses import dataclass

from app.models import db
from .user import User


@dataclass
class Player:
    id: int
    user: User

    @classmethod
    def from_db(cls, player: db.Player, user: User) -> Player:
        return cls(
            id=player.id,
            user=user,
        )
