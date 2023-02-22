from __future__ import annotations

from dataclasses import dataclass

from .user import User


@dataclass
class Player:
    id: int
    can_be_author: bool
    is_dummy: bool
    user: User | None

    @property
    def name_mention(self) -> str:
        if self.is_dummy:
            return f"dummy-{self.id}"
        return self.user.name_mention

    def get_tech_chat_id(self, reserve_chat_id: int) -> int:
        return reserve_chat_id if self.is_dummy else self.get_chat_id()

    def get_chat_id(self) -> int | None:
        if self.is_dummy:
            return None
        return self.user.tg_id

    def get_tg_username(self) -> str | None:
        if self.is_dummy:
            return None
        return self.user.username
