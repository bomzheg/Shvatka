from sqlalchemy import Column, Integer, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.models.db import Base


class PlayerInTeam(Base):
    __tablename__ = "users_in_teams"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey("players.id"), nullable=False)
    user = relationship(
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
    date_joined = Column(DateTime)
    role = Column(Text)
    _emoji = Column("emoji", Text)
    date_left = Column(DateTime)

    can_manage_waivers = Column(Boolean, default=False)
    can_manage_players = Column(Boolean, default=False)
    can_change_team_name = Column(Boolean, default=False)
    can_add_players = Column(Boolean, default=False)
    can_remove_players = Column(Boolean, default=False)
