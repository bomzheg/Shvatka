from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, mapped_column, Mapped

from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.models import Base


class LevelTime(Base):
    __tablename__ = "levels_times"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="level_times",
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="completed_levels",
    )
    level_number: Mapped[int] = mapped_column(Integer)
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=tz_utc),
        server_default=func.now(),
        nullable=False,
    )

    def to_dto(self, game: dto.Game, team: dto.Team) -> dto.LevelTime:
        return dto.LevelTime(
            id=self.id,
            game=game,
            team=team,
            level_number=self.level_number,
            start_at=self.start_at,
        )
