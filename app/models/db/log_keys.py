from sqlalchemy import Column, Integer, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.models.db import Base


class KeyTime(Base):
    __tablename__ = "log_keys"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    user = relationship(
        "User",
        foreign_keys=user_id,
        back_populates="typed_keys",
    )
    team_id = Column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="typed_keys",
    )
    game_id = Column(ForeignKey("games.id"), nullable=False)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="log_keys",
    )
    level_number = Column(Integer)
    enter_time = Column(DateTime)
    key_text = Column(Text)
    is_correct: bool | None = Column(Boolean, nullable=True)
