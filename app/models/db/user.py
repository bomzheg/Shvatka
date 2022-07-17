from sqlalchemy import Column, Text, BigInteger, Boolean
from sqlalchemy.orm import relationship

from app.models.db.base import Base


class User(Base):
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(BigInteger, primary_key=True)
    tg_id = Column(BigInteger, unique=True)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    username = Column(Text, nullable=True)
    is_bot = Column(Boolean, default=False)

    my_games = relationship(
        "Game",
        back_populates="author",
        foreign_keys="Game.author_id",
    )
    my_levels = relationship(
        "Level",
        back_populates="author",
        foreign_keys="Level.author_id",
    )
    typed_keys = relationship(
        "KeyTime",
        back_populates="user",
        foreign_keys="KeyTime.user_id",
    )
    organizers = relationship(
        "Organizer",
        back_populates="user",
        foreign_keys="Organizer.user_id",
    )
    played_games = relationship(
        "Waiver",
        back_populates="user",
        foreign_keys="Waiver.user_id",
    )

    def __repr__(self):
        rez = (
            f"<User "
            f"id={self.id} "
            f"tg_id={self.tg_id} "
            f"name={self.first_name} {self.last_name} "
        )
        if self.username:
            rez += f"username=@{self.username}"
        return rez + ">"
