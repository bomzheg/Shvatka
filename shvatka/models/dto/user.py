from __future__ import annotations

from dataclasses import dataclass

from aiogram import types as tg


@dataclass
class User:
    tg_id: int | None = None
    db_id: int | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_bot: bool | None = None

    @property
    def fullname(self) -> str:
        if self.first_name is None:
            return ""
        if self.last_name is not None:
            return " ".join((self.first_name, self.last_name))
        return self.first_name

    @property
    def name_mention(self) -> str:
        return self.fullname or self.username or str(self.tg_id) or str(self.db_id) or "unknown"

    @classmethod
    def from_aiogram(cls, user: tg.User) -> User:
        return cls(
            tg_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_bot=user.is_bot,
        )

    def add_password(self, hashed_password: str) -> UserWithCreds:
        return UserWithCreds(
            tg_id=self.tg_id,
            db_id=self.db_id,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            is_bot=self.is_bot,
            hashed_password=hashed_password,
        )


@dataclass
class UserWithCreds(User):
    hashed_password: str | None = None

    def without_password(self) -> User:
        return User(
            tg_id=self.tg_id,
            db_id=self.db_id,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            is_bot=self.is_bot,
        )
