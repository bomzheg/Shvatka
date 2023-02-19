from __future__ import annotations

from dataclasses import dataclass

from .user import User


@dataclass
class Player:
    id: int
    can_be_author: bool
    is_dummy: bool
    user: User

    @property
    def name_mention(self) -> str:
        return self.user.name_mention
