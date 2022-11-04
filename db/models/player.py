from sqlalchemy import Column, BigInteger, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from db.models.base import Base
from shvatka.models import dto


class Player(Base):
    __tablename__ = "players"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(BigInteger, primary_key=True)
    can_be_author = Column(Boolean, server_default="f", nullable=False)
    promoted_by_id = Column(ForeignKey("players.id"))
    user_id = Column(ForeignKey("users.id"), unique=True)
    user = relationship(
        "User",
        back_populates="player",
        foreign_keys=user_id,
        uselist=False,
    )

    my_games = relationship(
        "Game",
        back_populates="author",
        foreign_keys="Game.author_id",
    )
    my_levels = relationship(
        "Level",
        back_populates="author",
        foreign_keys="Level.author_id",
    )
    typed_keys = relationship(
        "KeyTime",
        back_populates="player",
        foreign_keys="KeyTime.player_id",
    )
    organizers = relationship(
        "Organizer",
        back_populates="player",
        foreign_keys="Organizer.player_id",
    )
    played_games = relationship(
        "Waiver",
        back_populates="player",
        foreign_keys="Waiver.player_id",
    )
    teams = relationship(
        "PlayerInTeam",
        back_populates="player",
        foreign_keys="PlayerInTeam.player_id",
    )
    captain_by_team = relationship(
        "Team",
        back_populates="captain",
        foreign_keys="Team.captain_id",
    )
    my_files = relationship(
        "FileInfo",
        back_populates="author",
        foreign_keys="FileInfo.author_id",
    )

    def __repr__(self):
        return (
            f"<Player "
            f"id={self.id} "
            f"user_id={self.user_id} "
            f">"
        )

    def to_dto(self, user: dto.User) -> dto.Player:
        return dto.Player(
            id=self.id,
            user=user,
            can_be_author=self.can_be_author,
        )
