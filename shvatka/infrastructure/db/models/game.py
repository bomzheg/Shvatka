from __future__ import annotations

import secrets
import typing
from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    Text,
    Enum,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from shvatka.core.models import dto
from shvatka.core.models.enums.game_status import GameStatus
from shvatka.infrastructure.db.models import Base

if typing.TYPE_CHECKING:
    from .. import models

_TOKEN_LEN = 32  # обязательно кратно 4


class Game(Base):
    __tablename__ = "games"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    author: Mapped[models.Player] = relationship(
        "Player",
        foreign_keys=author_id,
        back_populates="my_games",
    )
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus, name="game_status"),
        server_default=GameStatus.underconstruction,
        nullable=False,
    )
    levels: Mapped[list[models.Level]] = relationship(
        "Level",
        back_populates="game",
        foreign_keys="Level.game_id",
        order_by="Level.number_in_game",
    )
    level_times: Mapped[list[models.LevelTime]] = relationship(
        "LevelTime",
        back_populates="game",
        foreign_keys="LevelTime.game_id",
    )
    log_keys: Mapped[list[models.KeyTime]] = relationship(
        "KeyTime",
        back_populates="game",
        foreign_keys="KeyTime.game_id",
    )
    organizers: Mapped[list[models.Organizer]] = relationship(
        "Organizer", back_populates="game", foreign_keys="Organizer.game_id"
    )
    waivers: Mapped[list[models.Waiver]] = relationship(
        "Waiver",
        back_populates="game",
        foreign_keys="Waiver.game_id",
    )
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    manage_token: Mapped[str] = mapped_column(
        Text,
        default=lambda: secrets.token_urlsafe(_TOKEN_LEN * 3 // 4),
    )
    number: Mapped[int | None]
    published_channel_id: Mapped[int | None] = mapped_column(nullable=True)
    results_picture_file_id: Mapped[str | None] = mapped_column(nullable=True)
    keys_url: Mapped[str | None] = mapped_column(nullable=True)

    __table_args__ = (UniqueConstraint("author_id", "name"),)

    def to_dto(self, author: dto.Player) -> dto.Game:
        return dto.Game(
            id=self.id,
            author=author,
            name=self.name,
            status=self.status,
            start_at=self.start_at,
            manage_token=self.manage_token,
            number=self.number,
            results=dto.GameResults(
                published_chanel_id=self.published_channel_id,
                results_picture_file_id=self.results_picture_file_id,
                keys_url=self.keys_url,
            ),
        )

    def to_full_dto(self, author: dto.Player, levels: list[dto.Level]) -> dto.FullGame:
        return self.to_dto(author).to_full_game(levels)
