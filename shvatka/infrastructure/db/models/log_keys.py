from datetime import datetime

from sqlalchemy import Integer, ForeignKey, Text, Boolean, DateTime, func
from sqlalchemy.orm import relationship, mapped_column, Mapped

from shvatka.core.models import dto, enums
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.models import Base


class KeyTime(Base):
    __tablename__ = "log_keys"
    __mapper_args__ = {"eager_defaults": True}
    id = mapped_column(Integer, primary_key=True)
    player_id = mapped_column(ForeignKey("players.id"), nullable=False)
    player = relationship(
        "Player",
        foreign_keys=player_id,
        back_populates="typed_keys",
    )
    team_id = mapped_column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="typed_keys",
    )
    game_id = mapped_column(ForeignKey("games.id"), nullable=False)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="log_keys",
    )
    level_number = mapped_column(Integer, nullable=False)
    enter_time = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=tz_utc),
        server_default=func.now(),
        nullable=False,
    )
    key_text = mapped_column(Text, nullable=False)
    type_: Mapped[enums.KeyType] = mapped_column("type", Text, nullable=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False)

    def to_dto(self, player: dto.Player, team: dto.Team) -> dto.KeyTime:
        return dto.KeyTime(
            text=self.key_text,
            type_=self.type_,
            is_duplicate=self.is_duplicate,
            at=self.enter_time,
            level_number=self.level_number,
            player=player,
            team=team,
        )
