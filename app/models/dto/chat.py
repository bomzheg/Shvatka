from __future__ import annotations

from dataclasses import dataclass

from aiogram import types as tg

from app.enums.chat_type import ChatType
from app.models import db


@dataclass
class Chat:
    tg_id: int
    type: ChatType
    db_id: int | None = None
    username: str | None = None
    title: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    @property
    def full_name(self):
        return self.first_name + " " + self.last_name or ""

    @property
    def name(self):
        if self.type == ChatType.private:
            return self.full_name
        return self.title

    @classmethod
    def from_aiogram(cls, chat: tg.Chat) -> Chat:
        return cls(
            tg_id=chat.id,
            title=chat.title,
            type=ChatType[chat.type],
            username=chat.username,
            first_name=chat.first_name,
            last_name=chat.last_name,
        )

    @classmethod
    def from_db(cls, chat: db.Chat) -> Chat:
        return cls(
            tg_id=chat.tg_id,
            db_id=chat.id,
            title=chat.title,
            type=chat.type,
            username=chat.username,
        )
