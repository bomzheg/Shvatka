from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.models.db import Base


class Team(Base):
    __tablename__ = "teams"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    chat_id = Column(ForeignKey("chats.id"))
    chat = relationship(
        "Chat",
        foreign_keys=chat_id,
        back_populates="team",
    )
    captain_id = Column(ForeignKey("players.id"))
    captain = relationship(
        "Player",
        foreign_keys=captain_id,
        back_populates="captain_by_team",
    )
    description = Column(Text)

    completed_levels = relationship(
        "LevelTime",
        back_populates="team",
        foreign_keys="LevelTime.team_id",
    )
    typed_keys = relationship(
        "KeyTime",
        back_populates="team",
        foreign_keys="KeyTime.team_id",
    )
    played_games = relationship(
        "Waiver",
        back_populates="team",
        foreign_keys="Waiver.team_id",
    )
