import typing
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Self, overload

from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus

T = typing.TypeVar("T")


@dataclass
class Page(Generic[T]):
    content: Sequence[T]


@dataclass
class Items(Generic[T]):
    items: Sequence[T]


@dataclass
class Player:
    id: int
    can_be_author: bool
    name_mention: str
    username: str | None

    @classmethod
    def from_core(cls, core: dto.Player) -> Self:
        return cls(
            id=core.id,
            can_be_author=core.can_be_author,
            name_mention=core.name_mention,
            username=core.username,
        )


@dataclass
class Team:
    id: int
    name: str
    captain: Player | None
    description: str | None

    @overload
    @classmethod
    def from_core(cls, core: dto.Team) -> Self:
        ...

    @overload
    @classmethod
    def from_core(cls, core: None) -> None:
        ...

    @classmethod
    def from_core(cls, core: dto.Team | None) -> "Self | None":
        if core is None:
            return None
        return cls(
            id=core.id,
            name=core.name,
            captain=Player.from_core(core.captain) if core.captain else None,
            description=core.description,
        )


@dataclass
class Game:
    id: int
    author: Player
    name: str
    status: GameStatus
    start_at: datetime | None = None
    number: int | None = None

    @overload
    @classmethod
    def from_core(cls, core: dto.Game) -> Self:
        ...

    @overload
    @classmethod
    def from_core(cls, core: None) -> None:
        ...

    @classmethod
    def from_core(cls, core: dto.Game | None) -> "Self | None":
        if core is None:
            return None
        return cls(
            id=core.id,
            author=Player.from_core(core.author),
            name=core.name,
            status=core.status,
            start_at=core.start_at,
            number=core.number,
        )


@dataclass
class TgUser:
    tg_id: int
    username: str | None
    first_name: str | None
    last_name: str | None

    @classmethod
    def from_core(cls, core: dto.User | None) -> "TgUser | None":
        if core is None:
            return None
        return cls(
            tg_id=core.tg_id,
            username=core.username,
            first_name=core.first_name,
            last_name=core.last_name,
        )


@dataclass
class ForumUser:
    name: str

    @classmethod
    def from_core(cls, core: dto.ForumUser | None) -> "ForumUser | None":
        if core is None:
            return None
        return cls(name=core.name)


@dataclass
class EmailAccount:
    email: str
    is_verified: bool

    @classmethod
    def from_core(cls, core: dto.EmailAccount | None) -> "EmailAccount | None":
        if core is None:
            return None
        return cls(email=core.email, is_verified=core.is_verified)
