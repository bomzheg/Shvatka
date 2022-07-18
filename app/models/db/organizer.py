from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.models.db import Base


class Organizer(Base):
    __tablename__ = "organizers"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey("players.id"), nullable=False)
    player = relationship(
        "Player",
        foreign_keys=player_id,
        back_populates="organizers",
    )
    game_id = Column(ForeignKey("games.id"), nullable=False)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="organizers",
    )
    can_spy = Column(Boolean, default=False)
    can_see_log_keys = Column(Boolean, default=False)
    can_validate_waivers = Column(Boolean, default=False)
    deleted = Column(Boolean, default=False)
