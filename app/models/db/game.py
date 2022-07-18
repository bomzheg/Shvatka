from __future__ import annotations

import enum
import secrets

from sqlalchemy import Column, Integer, ForeignKey, Text, Enum, BigInteger, DateTime
from sqlalchemy.orm import relationship

from app.models.db import Base

_TOKEN_LEN = 32  # обязательно кратно 4


class GameStatus(str, enum.Enum):
    underconstruction = 'underconstruction'
    ready = 'ready'
    getting_waivers = 'getting_waivers'
    started = 'started'
    finished = 'finished'
    complete = 'complete'


class Game(Base):
    __tablename__ = "games"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    author_id = Column(ForeignKey("players.id"), nullable=False)
    author = relationship(
        "Player",
        foreign_keys=author_id,
        back_populates="my_games",
    )
    name = Column(Text)
    status = Column(Enum(GameStatus))
    levels = relationship(
        "Level",
        back_populates="game",
        foreign_keys="Level.game_id",
    )
    level_times = relationship(
        "LevelTime",
        back_populates="game",
        foreign_keys="LevelTime.game_id",
    )
    log_keys = relationship(
        "KeyTime",
        back_populates="game",
        foreign_keys="KeyTime.game_id",
    )
    organizers = relationship(
        "Organizer",
        back_populates="game",
        foreign_keys="Organizer.game_id"
    )
    waivers = relationship(
        "Waiver",
        back_populates="game",
        foreign_keys="Waiver.game_id",
    )
    start_at = Column(DateTime)
    published_channel_id = Column(BigInteger)
    manage_token = Column(Text, default=secrets.token_urlsafe(_TOKEN_LEN*3//4))


status_desc = {
    GameStatus.underconstruction: 'в процессе создания',
    GameStatus.ready: 'полностью готова',
    GameStatus.getting_waivers: 'сбор вейверов',
    GameStatus.started: 'началась',
    GameStatus.finished: 'все команды финишировали',
    GameStatus.complete: 'завершена'
}
active_statuses = [
    GameStatus.getting_waivers,
    GameStatus.started,
    GameStatus.finished
]
