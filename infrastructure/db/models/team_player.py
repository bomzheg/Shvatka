from datetime import datetime

from sqlalchemy import Integer, ForeignKey, Text, Boolean, DateTime, func
from sqlalchemy.orm import relationship, mapped_column

from infrastructure.db.models import Base
from shvatka.models import dto
from shvatka.utils.datetime_utils import tz_utc


class TeamPlayer(Base):
    __tablename__ = "team_players"
    __mapper_args__ = {"eager_defaults": True}
    id = mapped_column(Integer, primary_key=True)
    player_id = mapped_column(ForeignKey("players.id"), nullable=False)
    player = relationship(
        "Player",
        foreign_keys=player_id,
        back_populates="teams",
    )
    team_id = mapped_column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="players",
    )
    date_joined = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=tz_utc),
        server_default=func.now(),
        nullable=False,
    )
    role = mapped_column(Text)
    emoji = mapped_column("emoji", Text)
    date_left = mapped_column(DateTime(timezone=True))

    can_manage_waivers = mapped_column(Boolean, default=False, nullable=False)
    can_manage_players = mapped_column(Boolean, default=False, nullable=False)
    can_change_team_name = mapped_column(Boolean, default=False, nullable=False)
    can_add_players = mapped_column(Boolean, default=False, nullable=False)
    can_remove_players = mapped_column(Boolean, default=False, nullable=False)

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
