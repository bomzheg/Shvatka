from __future__ import annotations

from dataclasses import dataclass, field, InitVar

from .forum_user import ForumUser
from .user import User


@dataclass
class Player:
    id: int
    can_be_author: bool
    is_dummy: bool
    username: str | None = field(default=None)
    user: InitVar[User | None] = field(default=None)
    _user: User | None = field(init=False)
    forum_user: InitVar[ForumUser | None] = field(default=None)
    _forum_user: ForumUser | None = field(init=False)

    def __post_init__(self, user: User | None, forum_user: ForumUser | None):
        self._user = user
        self._forum_user = forum_user

    @property
    def name_mention(self) -> str:
        if self.username is not None:
            return self.username
        if self.is_dummy:
            if self._forum_user:
                return self._forum_user.name_mention
            return f"dummy-{self.id}"
        if self.has_user():
            assert self._user, f"only tg users supported, got forum user, {self!r}"
            return self._user.name_mention
        return f"player_id{self.id}"

    def has_user(self) -> bool:
        return self._user is not None

    def has_forum_user(self) -> bool:
        return self._forum_user is not None

    def get_tech_chat_id(self, reserve_chat_id: int) -> int:
        if self.is_dummy:
            return reserve_chat_id
        chat_id = self.get_chat_id()
        assert chat_id, f"chat_id required, got, {self!r}"
        return chat_id

    def get_chat_id(self) -> int | None:
        if self.is_dummy:
            return None
        assert self._user, f"only tg users supported, got forum user, {self!r}"
        return self._user.tg_id

    def get_tg_username(self) -> str | None:
        if self.is_dummy:
            return None
        assert self._user, f"only tg users supported, got forum user, {self!r}"
        return self._user.username

    def get_forum_name(self) -> str | None:
        if self._forum_user is None:
            return None
        assert self._forum_user, f"only forum users supported, got tg user, {self!r}"
        return self._forum_user.name

    def with_stat(self, typed_keys_count: int, typed_correct_keys_count: int) -> PlayerWithStat:
        return PlayerWithStat(
            id=self.id,
            username=self.username,
            can_be_author=self.can_be_author,
            is_dummy=self.is_dummy,
            user=self._user,
            forum_user=self._forum_user,
            typed_keys_count=typed_keys_count,
            typed_correct_keys_count=typed_correct_keys_count,
        )

    def add_password(self, hashed_password: str) -> PlayerWithCreds:
        return PlayerWithCreds(
            id=self.id,
            can_be_author=self.can_be_author,
            is_dummy=self.is_dummy,
            username=self.username,
            hashed_password=hashed_password,
            user=self._user,
            forum_user=self._forum_user,
        )


@dataclass
class PlayerWithCreds(Player):
    hashed_password: str | None = None

    def without_password(self) -> Player:
        return Player(
            id=self.id,
            can_be_author=self.can_be_author,
            is_dummy=self.is_dummy,
            username=self.username,
            user=self._user,
            forum_user=self._forum_user,
        )


@dataclass
class PlayerWithStat(Player):
    typed_keys_count: int = 0
    typed_correct_keys_count: int = 0
