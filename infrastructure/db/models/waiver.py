from sqlalchemy import Integer, ForeignKey, Text, Enum, UniqueConstraint
from sqlalchemy.orm import relationship, mapped_column

from infrastructure.db.models import Base
from shvatka.models import dto
from shvatka.models.enums.played import Played


class Waiver(Base):
    __tablename__ = "waivers"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (UniqueConstraint("game_id", "team_id", "player_id"),)
    id = mapped_column(Integer, primary_key=True)
    player_id = mapped_column(ForeignKey("players.id"), nullable=False)
    player = relationship(
        "Player",
        foreign_keys=player_id,
        back_populates="played_games",
    )
    team_id = mapped_column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="played_games",
    )
    game_id = mapped_column(ForeignKey("games.id"), nullable=False)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="waivers",
    )
    role = mapped_column(Text)
    played = mapped_column(Enum(Played), nullable=False)

    def to_dto(self, player: dto.Player, team: dto.Team, game: dto.Game) -> dto.Waiver:
        return dto.Waiver(
            player=player,
            team=team,
            game=game,
            played=self.played,
        )
