from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, mapped_column, Mapped

from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.models import Base


class TeamPlayer(Base):
    __tablename__ = "team_players"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    player = relationship(
        "Player",
        foreign_keys=player_id,
        back_populates="teams",
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="players",
    )
    date_joined: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=tz_utc),
        server_default=func.now(),
        nullable=False,
    )
    role: Mapped[str]
    emoji: Mapped[str]
    date_left: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    can_manage_waivers: Mapped[bool] = mapped_column(default=False, nullable=False)
    can_manage_players: Mapped[bool] = mapped_column(default=False, nullable=False)
    can_change_team_name: Mapped[bool] = mapped_column(default=False, nullable=False)
    can_add_players: Mapped[bool] = mapped_column(default=False, nullable=False)
    can_remove_players: Mapped[bool] = mapped_column(default=False, nullable=False)

    def to_dto(self) -> dto.TeamPlayer:
        return dto.TeamPlayer(
            id=self.id,
            player_id=self.player_id,
            team_id=self.team_id,
            date_joined=self.date_joined,
            date_left=self.date_left,
            role=self.role,
            emoji=self.emoji,
            _can_manage_waivers=self.can_manage_waivers,
            _can_manage_players=self.can_manage_players,
            _can_change_team_name=self.can_change_team_name,
            _can_add_players=self.can_add_players,
            _can_remove_players=self.can_remove_players,
        )
