from sqlalchemy import BigInteger, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, mapped_column, Mapped

from shvatka.core.models import dto
from shvatka.infrastructure.db.models.base import Base


class EmailAccount(Base):
    __tablename__ = "emails"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, server_default="f", nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), unique=True, nullable=False)

    player = relationship(
        "Player",
        back_populates="email",
        foreign_keys=player_id,
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<EmailAccount id={self.id} email={self.email} verified={self.is_verified} >"

    def to_dto(self) -> dto.EmailAccount:
        return dto.EmailAccount(
            db_id=self.id,
            email=self.email,
            is_verified=self.is_verified,
            player_id=self.player_id,
        )
