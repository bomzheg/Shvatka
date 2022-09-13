from __future__ import annotations

from dataclasses import dataclass

from aiogram import types as tg

from shvatka.models import db


@dataclass
class User:
    tg_id: int
    db_id: int | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_bot: bool | None = None

    @property
    def fullname(self) -> str:
        if self.last_name is not None:
            return ' '.join((self.first_name, self.last_name))
        return self.first_name

    @property
    def name_mention(self) -> str:
        return self.fullname or self.username or self.tg_id

    @classmethod
    def from_aiogram(cls, user: tg.User) -> User:
        return cls(
            tg_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_bot=user.is_bot,
        )

    @classmethod
    def from_db(cls, user: db.User) -> User:
        return cls(
            db_id=user.id,
            tg_id=user.tg_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_bot=user.is_bot,
        )
