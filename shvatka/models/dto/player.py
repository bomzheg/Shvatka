from __future__ import annotations

from dataclasses import dataclass

from .user import User


@dataclass
class Player:
    id: int
    can_be_author: bool
    is_dummy: bool
    user: User
