import logging
import typing
from typing import Any

from adaptix import Retort, dumper, P
from sqlalchemy import Integer, Text, ForeignKey, JSON, TypeDecorator, UniqueConstraint
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import relationship, mapped_column, Mapped

from shvatka.common.factory import REQUIRED_GAME_RECIPES
from shvatka.core.models import dto
from shvatka.core.models.dto import scn, action
from shvatka.infrastructure.db.models import Base

if typing.TYPE_CHECKING:
    from .game import Game
    from .player import Player

logger = logging.getLogger(__name__)


class ScenarioField(TypeDecorator):
    impl = JSON
    cache_ok = True
    retort = Retort(
        recipe=[
            *REQUIRED_GAME_RECIPES,
        ],
    )

    def coerce_compared_value(self, op: Any, value: Any):
        if isinstance(value, scn.LevelScenario):
            return self
        return self.impl().coerce_compared_value(op=op, value=value)

    def process_bind_param(self, value: scn.LevelScenario | None, dialect: Dialect):
        try:
            dumped = self.retort.dump(value, scn.LevelScenario)
        except Exception as e:
            logger.exception("can't dump level scenario", exc_info=e)
            raise
        return dumped

    def process_result_value(self, value: Any, dialect: Dialect) -> scn.LevelScenario | None:
        if value is None:
            return None
        return self.retort.load(value, scn.LevelScenario)


class Level(Base):
    __tablename__ = "levels"
    __mapper_args__ = {"eager_defaults": True}
    id = mapped_column(Integer, primary_key=True)
    name_id: Mapped[str] = mapped_column(Text, nullable=False)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=True)
    game: Mapped["Game"] = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="levels",
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    author: Mapped["Player"] = relationship(
        "Player",
        foreign_keys=author_id,
        back_populates="my_levels",
    )
    number_in_game = mapped_column(Integer, nullable=True)
    scenario: Mapped[scn.LevelScenario] = mapped_column(ScenarioField)

    __table_args__ = (UniqueConstraint("author_id", "name_id"),)

    def to_dto(self, author: dto.Player) -> dto.Level:
        return dto.Level(
            db_id=self.id,
            name_id=self.name_id,
            author=author,
            scenario=self.scenario,
            game_id=self.game_id,
            number_in_game=self.number_in_game,
        )
