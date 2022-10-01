from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, Text, Boolean, DateTime, func
from sqlalchemy.orm import relationship

from db.models import Base


class PlayerInTeam(Base):
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
    date_joined = Column(DateTime, default=datetime.utcnow(), server_default=func.now())
    role = Column(Text)
    emoji = Column("emoji", Text)
    date_left = Column(DateTime)

    can_manage_waivers = Column(Boolean, default=False)
    can_manage_players = Column(Boolean, default=False)
    can_change_team_name = Column(Boolean, default=False)
    can_add_players = Column(Boolean, default=False)
    can_remove_players = Column(Boolean, default=False)
