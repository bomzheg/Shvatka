from db.models import Base
from shvatka.models import dto
from sqlalchemy import Column, Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship


class Organizer(Base):
    __tablename__ = "organizers"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    player_id = Column(ForeignKey("players.id"), nullable=False)
    player = relationship(
        "Player",
        foreign_keys=player_id,
        back_populates="organizers",
    )
    game_id = Column(ForeignKey("games.id"), nullable=False)
    game = relationship(
        "Game",
        foreign_keys=game_id,
        back_populates="organizers",
    )
    can_spy = Column(Boolean, default=False)
    can_see_log_keys = Column(Boolean, default=False)
    can_validate_waivers = Column(Boolean, default=False)
    deleted = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("player_id", "game_id"),
    )

    def to_dto(self, player: dto.Player, game: dto.Game) -> dto.SecondaryOrganizer:
        return dto.SecondaryOrganizer(
            id=self.id,
            player=player,
            game=game,
            can_spy=self.can_spy,
            can_see_log_keys=self.can_see_log_keys,
            can_validate_waivers=self.can_validate_waivers,
            deleted=self.deleted,
        )
