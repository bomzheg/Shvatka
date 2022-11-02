from sqlalchemy import Column, Integer, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import relationship

from db.models import Base
from shvatka.models import dto


class KeyTime(Base):
    __tablename__ = "log_keys"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey("players.id"), nullable=False)
    player = relationship(
        "Player",
        foreign_keys=player_id,
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
    enter_time = Column(DateTime(timezone=True))
    key_text = Column(Text)
    is_correct: bool = Column(Boolean, nullable=False)
    is_duplicate: bool = Column(Boolean, nullable=False)

    def to_dto(self, player: dto.Player, team: dto.Team) -> dto.KeyTime:
        return dto.KeyTime(
            text=self.key_text,
            is_correct=self.is_correct,
            is_duplicate=self.is_duplicate,
            at=self.enter_time,
            level_number=self.level_number,
            player=player,
            team=team,
        )
