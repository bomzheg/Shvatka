from sqlalchemy import Column, Integer, ForeignKey, Text, Enum, UniqueConstraint
from sqlalchemy.orm import relationship

from infrastructure.db.models import Base
from shvatka.models import dto
from shvatka.models.enums.played import Played


class Waiver(Base):
    __tablename__ = "waivers"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (UniqueConstraint("game_id", "team_id", "player_id"),)
    id = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey("players.id"), nullable=False)
    player = relationship(
        "Player",
        foreign_keys=player_id,
        back_populates="played_games",
    )
    team_id = Column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="played_games",
    )
    game_id = Column(ForeignKey("games.id"), nullable=False)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="waivers",
    )
    role = Column(Text)
    played = Column(Enum(Played), nullable=False)

    def to_dto(self, player: dto.Player, team: dto.Team, game: dto.Game) -> dto.Waiver:
        return dto.Waiver(
            player=player,
            team=team,
            game=game,
            played=self.played,
        )
