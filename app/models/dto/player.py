from __future__ import annotations

from dataclasses import dataclass

from app.models import db
from .user import User


@dataclass
class Player:
    id: int
    user: User

    @staticmethod
    def from_db(player: db.Player, user: User) -> Player:
        return Player(
            id=player.id,
            user=user,
        )
