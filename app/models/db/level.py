from sqlalchemy import Column, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.db import Base


class Level(Base):
    __tablename__ = "levels"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    name_id = Column(Text)
    game_id = Column(ForeignKey("games.id"), nullable=True)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="levels",
    )
    author_id = Column(ForeignKey("users.id"), nullable=False)
    author = relationship(
        "User",
        foreign_keys=author_id,
        back_populates="my_levels",
    )
    number_in_game = Column(Integer, nullable=True)
    scenario = Column(JSON)  # TODO load json to dataclass?
