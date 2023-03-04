from sqlalchemy import ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship, mapped_column, Mapped

from src.infrastructure.db.models import Base
from src.shvatka.models import dto
from src.shvatka.models.enums.played import Played


class Waiver(Base):
    __tablename__ = "waivers"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (UniqueConstraint("game_id", "team_id", "player_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    player = relationship(
        "Player",
        foreign_keys=player_id,
        back_populates="played_games",
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    team = relationship(
        "Team",
        foreign_keys=team_id,
        back_populates="played_games",
    )
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), nullable=False)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="waivers",
    )
    role: Mapped[str]
    played: Mapped[Played] = mapped_column(Enum(Played), nullable=False)

    def to_dto(self, player: dto.Player, team: dto.Team, game: dto.Game) -> dto.Waiver:
        return dto.Waiver(
            player=player,
            team=team,
            game=game,
            played=self.played,
        )
