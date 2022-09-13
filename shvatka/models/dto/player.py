from __future__ import annotations

from dataclasses import dataclass

from shvatka.models import db
from .user import User


@dataclass
class Player:
    id: int
    can_be_author: bool
    user: User

    @classmethod
    def from_db(cls, player: db.Player, user: User) -> Player:
        return cls(
            id=player.id,
            user=user,
            can_be_author=player.can_be_author,
        )
