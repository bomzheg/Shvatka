from __future__ import annotations

from dataclasses import dataclass, field, InitVar

from .forum_user import ForumUser
from .user import User


@dataclass
class Player:
    id: int
    can_be_author: bool
    is_dummy: bool
    user: InitVar[User | None] = field(default=None)
    _user: User | None = field(init=False)
    forum_user: InitVar[ForumUser | None] = field(default=None)
    _forum_user: ForumUser | None = field(init=False)

    def __post_init__(self, user: User | None, forum_user: ForumUser | None):
        self._user = user
        self._forum_user = forum_user

    @property
    def name_mention(self) -> str:
        if self.is_dummy:
            return f"dummy-{self.id}"
        return self._user.name_mention

    def get_tech_chat_id(self, reserve_chat_id: int) -> int:
        return reserve_chat_id if self.is_dummy else self.get_chat_id()

    def get_chat_id(self) -> int | None:
        if self.is_dummy:
            return None
        return self._user.tg_id

    def get_tg_username(self) -> str | None:
        if self.is_dummy:
            return None
        return self._user.username
