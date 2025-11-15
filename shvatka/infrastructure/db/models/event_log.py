import logging
from datetime import datetime
from typing import Any

from adaptix import Retort
from sqlalchemy import Integer, ForeignKey, Text, Boolean, DateTime, func, TypeDecorator, Dialect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, mapped_column, Mapped

from shvatka.common.factory import REQUIRED_GAME_RECIPES
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import action
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.models import Base


logger = logging.getLogger(__name__)


class EffectsField(TypeDecorator):
    impl = JSONB
    cache_ok = True
    retort = Retort(
        recipe=[
            *REQUIRED_GAME_RECIPES,
        ],
    )

    def coerce_compared_value(self, op: Any, value: Any):
        if isinstance(value, action.Effects):
            return self
        return self.impl().coerce_compared_value(op=op, value=value)

    def process_bind_param(self, value: action.Effects | None, dialect: Dialect):
        try:
            dumped = self.retort.dump(value, action.Effects)
        except Exception as e:
            logger.exception("can't dump effects", exc_info=e)
            raise
        return dumped

    def process_result_value(self, value: Any, dialect: Dialect) -> action.Effects | None:
        if value is None:
            return None
        try:
            return self.retort.load(value, action.Effects)
        except Exception:
            logger.error("can't load effects from %s", value)
            raise


class GameEvent(Base):
    __tablename__ = "event_log"
    __mapper_args__ = {"eager_defaults": True}
    id = mapped_column(Integer, primary_key=True)
    team_id = mapped_column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
    )
    game_id = mapped_column(ForeignKey("games.id"), nullable=False)
    game = relationship(
        "Game",
        foreign_keys=game_id,
    )
    level_number = mapped_column(Integer, nullable=False)
    level_time_id = mapped_column(ForeignKey("levels_times.id"), nullable=False)
    at = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=tz_utc),
        server_default=func.now(),
        nullable=False,
    )
    effects: action.Effects = mapped_column(EffectsField, nullable=False)

    def to_dto(self, team: dto.Team) -> dto.GameEvent:
        return dto.GameEvent(
            at=self.at,
            level_number=self.level_number,
            level_team_id=self.level_time_id,
            team=team,
            effects=self.effects,
        )
