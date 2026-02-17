from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import mapped_column, relationship, Mapped

from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import tz_utc
from . import Base


class TimerAction(Base):
    __tablename__ = "timers_log"
    __mapper_args__ = {"eager_defaults": True}
    id = mapped_column(Integer, primary_key=True)
    level_time_id: Mapped[int] = mapped_column(ForeignKey("levels_times.id"), nullable=False)
    started_at = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=tz_utc),
        server_default=func.now(),
        nullable=False,
    )
    event_id = mapped_column(ForeignKey("event_log.id"), nullable=True)
    event = relationship(
        "GameEvent",
        foreign_keys=event_id,
    )

    def to_dto(self, event: dto.GameEvent) -> dto.Timer:
        assert event.id == self.event_id
        return dto.Timer(
            id=self.id,
            level_time_id=self.level_time_id,
            event=event,
        )
