from __future__ import annotations

import secrets

from sqlalchemy import (
    Column, Integer, ForeignKey, Text, Enum, BigInteger, DateTime, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from shvatka.models.db import Base
from shvatka.models.enums.game_status import GameStatus

_TOKEN_LEN = 32  # обязательно кратно 4


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
    status = Column(
        Enum(GameStatus),
        server_default=GameStatus.underconstruction,
        nullable=False,
    )
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
    manage_token = Column(
        Text,
        default=secrets.token_urlsafe(_TOKEN_LEN * 3 // 4),
    )

    __table_args__ = (
        UniqueConstraint("author_id", "name"),
    )
