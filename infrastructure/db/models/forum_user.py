from datetime import date

from sqlalchemy import Text, BigInteger, ForeignKey, Date
from sqlalchemy.orm import relationship, mapped_column, Mapped

from infrastructure.db.models.base import Base
from shvatka.models import dto


class ForumUser(Base):
    __tablename__ = "forum_users"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    forum_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    registered: Mapped[date] = mapped_column(Date)
    url: Mapped[str]
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), unique=True)

    player = relationship(
        "Player",
        back_populates="forum_user",
        foreign_keys=player_id,
        uselist=False,
    )

    def __repr__(self):
        return (
            f"<ForumUser " f"id={self.id} " f"forum_id={self.forum_id} " f"name={self.name} " f">"
        )

    def to_dto(self) -> dto.ForumUser:
        return dto.ForumUser(
            db_id=self.id,
            forum_id=self.forum_id,
            name=self.name,
            registered=self.registered,
        )
