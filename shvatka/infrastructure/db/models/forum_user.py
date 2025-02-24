from datetime import date

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped

from shvatka.core.models import dto
from shvatka.infrastructure.db.models.base import Base


class ForumUser(Base):
    __tablename__ = "forum_users"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    forum_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    registered: Mapped[date | None]
    url: Mapped[str | None]
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), unique=True)

    player = relationship(
        "Player",
        back_populates="forum_user",
        foreign_keys=player_id,
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<ForumUser id={self.id} forum_id={self.forum_id} name={self.name} >"

    def to_dto(self) -> dto.ForumUser:
        return dto.ForumUser(
            db_id=self.id,
            forum_id=self.forum_id,
            name=self.name,
            registered=self.registered,
            player_id=self.player_id,
        )
