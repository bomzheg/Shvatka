from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import relationship, mapped_column

from src.infrastructure.db.models import Base
from src.shvatka.models import dto
from src.shvatka.utils.datetime_utils import tz_utc


class LevelTime(Base):
    __tablename__ = "levels_times"
    __mapper_args__ = {"eager_defaults": True}
    id = mapped_column(Integer, primary_key=True)
    game_id = mapped_column(ForeignKey("games.id"), nullable=False)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="level_times",
    )
    team_id = mapped_column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="completed_levels",
    )
    level_number = mapped_column(Integer)
    start_at = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=tz_utc),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("game_id", "team_id", "level_number"),)

    def to_dto(self, game: dto.Game, team: dto.Team) -> dto.LevelTime:
        return dto.LevelTime(
            id=self.id,
            game=game,
            team=team,
            level_number=self.level_number,
            start_at=self.start_at,
        )
