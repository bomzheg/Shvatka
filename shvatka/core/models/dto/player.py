from __future__ import annotations

from dataclasses import InitVar, dataclass, field

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

    def __post_init__(self, user: User | None) -> None:
        self._user = user

    def username_is_dummy(self) -> bool:
        return self.username == f"id{self.id}"

    @property
    def name_mention(self) -> str:
        if self.username is not None and not self.username_is_dummy():
            return self.username
        if self.is_dummy:
            return f"dummy-{self.id}"
        if self.has_user():
            assert self._user, f"has_user() lied about {self!r}"
            return self._user.name_mention
        return f"id{self.id}"

    def has_user(self) -> bool:
        return self._user is not None

    def get_tech_chat_id(self, reserve_chat_id: int) -> int:
        return self.get_chat_id() or reserve_chat_id

    def get_chat_id(self) -> int | None:
        # player may have no telegram identity (dummy, forum-only or email-only)
        if self._user is None:
            return None
        return self._user.tg_id

    def get_tg_username(self) -> str | None:
        if self._user is None:
            return None
        return self._user.username

    def get_tg_fullname(self) -> str | None:
        if self._user is None:
            return None
        return self._user.fullname or None

    def with_stat(self, typed_keys_count: int, typed_correct_keys_count: int) -> PlayerWithStat:
        return PlayerWithStat(
            id=self.id,
            username=self.username,
            can_be_author=self.can_be_author,
            is_dummy=self.is_dummy,
            user=self._user,
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
        )


@dataclass
class PlayerWithForum(Player):
    """A player together with their forum identity.

    Reading the forum account means joining ``forum_users``, and almost nothing
    needs it: a player carries their own ``username``, and telegram links come
    from ``_user``. So only the paths that actually render or check the forum
    account ask for this type — the profile, the admin panel, global search,
    the merge flow and forum-driven lookups — and everywhere else a plain
    :class:`Player` is loaded without touching the forum table.
    """

    forum_user: ForumUser | None = None

    @property
    def name_mention(self) -> str:
        # a forum-imported dummy saved before usernames existed has nothing else to show
        if (
            self.is_dummy
            and self.forum_user is not None
            and (self.username is None or self.username_is_dummy())
        ):
            return self.forum_user.name_mention
        return super().name_mention

    def has_forum_user(self) -> bool:
        return self.forum_user is not None

    def get_forum_name(self) -> str | None:
        if self.forum_user is None:
            return None
        return self.forum_user.name


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
        )


@dataclass
class PlayerWithStat(Player):
    typed_keys_count: int = 0
    typed_correct_keys_count: int = 0
