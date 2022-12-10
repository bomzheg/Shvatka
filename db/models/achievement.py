from datetime import datetime

from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, func, Enum, Boolean
from sqlalchemy.orm import relationship

from db.models.base import Base
from shvatka.models import enums, dto
from shvatka.utils.datetime_utils import tz_utc


class Achievement(Base):
    __tablename__ = "achievements"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(BigInteger, primary_key=True)
    player_id = Column(ForeignKey("players.id"), nullable=False)
    player = relationship(
        "Player",
        foreign_keys=player_id,
        back_populates="achievements",
    )
    name = Column(
        Enum(enums.Achievement, native_enum=False, length=256, create_constraint=False),
        nullable=False,
    )
    at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=tz_utc),
        server_default=func.now(), nullable=False,
    )
    first = Column(Boolean, nullable=False, default=False, server_default="F")

    def to_dto(self, player: dto.Player) -> dto.Achievement:
        return dto.Achievement(
            player=player,
            name=self.name,
            at=self.at,
            first=self.first,
        )

