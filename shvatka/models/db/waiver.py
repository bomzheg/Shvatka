from sqlalchemy import Column, Integer, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship

from shvatka.models.db import Base
from shvatka.models.enums.played import Played


class Waiver(Base):
    __tablename__ = "waivers"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey("players.id"), nullable=False)
    player = relationship(
        "Player",
        foreign_keys=player_id,
        back_populates="played_games",
    )
    team_id = Column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="played_games",
    )
    game_id = Column(ForeignKey("games.id"), nullable=False)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="waivers",
    )
    role = Column(Text)
    played = Column(Enum(Played), nullable=True)
