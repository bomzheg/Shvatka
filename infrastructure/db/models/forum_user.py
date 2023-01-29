from sqlalchemy import Column, Text, BigInteger, ForeignKey, Date
from sqlalchemy.orm import relationship

from infrastructure.db.models.base import Base
from shvatka.models import dto


class ForumUser(Base):
    __tablename__ = "forum_users"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(BigInteger, primary_key=True)
    forum_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    registered = Column(Date, nullable=False)
    player_id = Column(ForeignKey("players.id"), unique=True)

    player = relationship(
        "Player",
        back_populates="forum_user",
        foreign_keys=player_id,
        uselist=False,
    )

    def __repr__(self):
        return f"<ForumUser " f"id={self.id} " f"forum_id={self.tg_id} " f"name={self.name} " f">"

    def to_dto(self) -> dto.ForumUser:
        return dto.ForumUser(
            db_id=self.id,
            forum_id=self.forum_id,
            name=self.name,
            registered=self.registered,
        )
