from typing import Any

from dataclass_factory import Factory
from sqlalchemy import Column, Integer, Text, ForeignKey, JSON, TypeDecorator, UniqueConstraint
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import relationship

from infrastructure.db.models import Base
from shvatka.models import dto
from shvatka.models.dto.scn.level import LevelScenario


class ScenarioField(TypeDecorator):
    impl = JSON
    cache_ok = True
    dcf = Factory()

    def coerce_compared_value(self, op: Any, value: Any):
        if isinstance(value, LevelScenario):
            return self
        return self.impl.coerce_compared_value(op, value)

    def process_bind_param(self, value: LevelScenario | None, dialect: Dialect):
        return self.dcf.dump(value, LevelScenario)

    def process_result_value(self, value: Any, dialect: Dialect) -> LevelScenario | None:
        if value is None:
            return None
        return self.dcf.load(value, LevelScenario)


class Level(Base):
    __tablename__ = "levels"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    name_id = Column(Text, nullable=False)
    game_id = Column(ForeignKey("games.id"), nullable=True)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="levels",
    )
    author_id = Column(ForeignKey("players.id"), nullable=False)
    author = relationship(
        "Player",
        foreign_keys=author_id,
        back_populates="my_levels",
    )
    number_in_game = Column(Integer, nullable=True)
    scenario: LevelScenario = Column(ScenarioField)

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
