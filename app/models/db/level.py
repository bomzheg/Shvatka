from typing import Any

from dataclass_factory import Factory
from sqlalchemy import Column, Integer, Text, ForeignKey, JSON, TypeDecorator
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import relationship

from app.models.db import Base
from app.models.dto.scn.level import LeveScenario


class ScenarioField(TypeDecorator):
    impl = JSON
    cache_ok = True
    dcf = Factory()

    def coerce_compared_value(self, op: Any, value: Any):
        if isinstance(value, LeveScenario):
            return self
        return self.impl.coerce_compared_value(op, value)

    def process_bind_param(self, value: LeveScenario | None, dialect: Dialect):
        return self.dcf.dump(value, LeveScenario)

    def process_result_value(self, value: Any, dialect: Dialect) -> LeveScenario | None:
        return self.dcf.load(value, LeveScenario)


class Level(Base):
    __tablename__ = "levels"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    name_id = Column(Text)
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
    scenario: LeveScenario = Column(ScenarioField)
