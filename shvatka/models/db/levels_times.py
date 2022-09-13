from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

from shvatka.models.db import Base


class LevelTime(Base):
    __tablename__ = "levels_times"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    game_id = Column(ForeignKey("games.id"), nullable=False)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="level_times",
    )
    team_id = Column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="completed_levels",
    )
    level_number = Column(Integer)
    start_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("game_id", "team_id", "level_number"),
    )
