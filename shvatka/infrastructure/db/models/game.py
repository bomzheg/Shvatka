from __future__ import annotations

import logging
import secrets
import typing
from datetime import datetime
from typing import Any

from adaptix import Retort
from sqlalchemy import (
    ForeignKey,
    Index,
    Text,
    Enum,
    DateTime,
    TypeDecorator,
    UniqueConstraint,
    BigInteger,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import relationship, Mapped, mapped_column

from shvatka.common.factory import REQUIRED_GAME_RECIPES
from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.core.models.enums.game_status import GameStatus
from shvatka.infrastructure.db.models import Base

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db import models

logger = logging.getLogger(__name__)

_TOKEN_LEN = 32  # обязательно кратно 4


_RELEASE_RETORT = Retort(
    recipe=[
        *REQUIRED_GAME_RECIPES,
    ],
)


class ReleaseField(TypeDecorator):
    """The body of a game's release — a plain list of hints — stored as jsonb.

    The banner that leads the release lives in its own column: the site needs
    to render it alone, above the header, without reading the rest.
    """

    impl = JSONB
    cache_ok = True
    retort = _RELEASE_RETORT

    def process_bind_param(self, value: list[hints.AnyHint] | None, dialect: Dialect):
        if value is None:
            return None
        try:
            return self.retort.dump(value, list[hints.AnyHint])
        except Exception as e:
            logger.error("can't dump game release", exc_info=e)
            raise

    def process_result_value(self, value: Any, dialect: Dialect) -> list[hints.AnyHint] | None:
        if value is None:
            return None
        try:
            return self.retort.load(value, list[hints.AnyHint])
        except Exception as e:
            logger.error("can't load game release from %s", value, exc_info=e)
            raise


class ReleaseBannerField(TypeDecorator):
    """The release's banner — a wide title picture with a caption — as jsonb."""

    impl = JSONB
    cache_ok = True
    retort = _RELEASE_RETORT

    def process_bind_param(self, value: hints.PhotoHint | None, dialect: Dialect):
        if value is None:
            return None
        try:
            return self.retort.dump(value, hints.PhotoHint)
        except Exception as e:
            logger.error("can't dump game release banner", exc_info=e)
            raise

    def process_result_value(self, value: Any, dialect: Dialect) -> hints.PhotoHint | None:
        if value is None:
            return None
        try:
            return self.retort.load(value, hints.PhotoHint)
        except Exception as e:
            logger.error("can't load game release banner from %s", value, exc_info=e)
            raise


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
    published_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    results_picture_file_id: Mapped[str | None] = mapped_column(nullable=True)
    keys_url: Mapped[str | None] = mapped_column(nullable=True)
    release: Mapped[list[hints.AnyHint] | None] = mapped_column(ReleaseField, nullable=True)
    release_banner: Mapped[hints.PhotoHint | None] = mapped_column(
        ReleaseBannerField, nullable=True
    )
    release_post: Mapped[dict[str, typing.Any] | None] = mapped_column(JSONB, nullable=True)
    """Where the bot posted the release. Never part of `to_dto` — see `GameDao`."""

    __table_args__ = (
        UniqueConstraint("author_id", "name"),
        # keep in step with ACTIVE_STATUSES: Postgres only uses a partial index
        # for a query whose predicate this one implies
        Index(
            "ix__games__active_status",
            "status",
            postgresql_where=text("status IN ('getting_waivers', 'started', 'finished')"),
        ),
    )

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

    def to_full_dto(self, author: dto.Player, levels: list[dto.GamedLevel]) -> dto.FullGame:
        return self.to_dto(author).to_full_game(levels)
