import typing
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, DateTime, func, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column

from infrastructure.db.models.base import Base
from shvatka.models import enums, dto
from shvatka.utils.datetime_utils import tz_utc

if typing.TYPE_CHECKING:
    from .player import Player


class Achievement(Base):
    __tablename__ = "achievements"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    player: Mapped["Player"] = relationship(
        "Player",
        foreign_keys=player_id,
        back_populates="achievements",
    )
    name: Mapped[enums.Achievement] = mapped_column(
        Enum(enums.Achievement, native_enum=False, length=256, create_constraint=False),
        nullable=False,
    )
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=tz_utc),
        server_default=func.now(),
        nullable=False,
    )
    first: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="F")

    def to_dto(self, player: dto.Player) -> dto.Achievement:
        return dto.Achievement(
            player=player,
            name=self.name,
            at=self.at,
            first=self.first,
        )
