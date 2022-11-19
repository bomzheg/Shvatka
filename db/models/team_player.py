from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, Text, Boolean, DateTime, func
from sqlalchemy.orm import relationship

from db.models import Base
from shvatka.models import dto
from shvatka.utils.datetime_utils import tz_utc


class TeamPlayer(Base):
    __tablename__ = "players_in_teams"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey("players.id"), nullable=False)
    player = relationship(
        "Player",
        foreign_keys=player_id,
        back_populates="teams",
    )
    team_id = Column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="players",
    )
    date_joined = Column(DateTime(timezone=True), default=datetime.now(tz=tz_utc), server_default=func.now())
    role = Column(Text)
    emoji = Column("emoji", Text)
    date_left = Column(DateTime(timezone=True))

    can_manage_waivers = Column(Boolean, default=False)
    can_manage_players = Column(Boolean, default=False)
    can_change_team_name = Column(Boolean, default=False)
    can_add_players = Column(Boolean, default=False)
    can_remove_players = Column(Boolean, default=False)

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