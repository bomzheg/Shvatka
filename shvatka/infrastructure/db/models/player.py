from sqlalchemy import BigInteger, ForeignKey, Boolean
from sqlalchemy.orm import relationship, mapped_column, Mapped

from shvatka.core.models import dto
from shvatka.infrastructure.db.models.base import Base


class Player(Base):
    __tablename__ = "players"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    can_be_author: Mapped[bool] = mapped_column(Boolean, server_default="f", nullable=False)
    promoted_by_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    is_dummy: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="f")
    user = relationship(
        "User",
        back_populates="player",
        foreign_keys="User.player_id",
        uselist=False,
    )
    forum_user = relationship(
        "ForumUser",
        back_populates="player",
        foreign_keys="ForumUser.player_id",
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
        "TeamPlayer",
        back_populates="player",
        foreign_keys="TeamPlayer.player_id",
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
    achievements = relationship(
        "Achievement",
        foreign_keys="Achievement.player_id",
        back_populates="player",
    )

    def __repr__(self):
        return f"<Player id={self.id} >"

    def to_dto(
        self, user: dto.User | None = None, forum_user: dto.ForumUser | None = None
    ) -> dto.Player:
        return dto.Player(
            id=self.id,
            user=user,
            forum_user=forum_user,
            can_be_author=self.can_be_author,
            is_dummy=self.is_dummy,
        )

    def to_dto_user_prefetched(self) -> dto.Player:
        return self.to_dto(
            user=self.user.to_dto() if self.user else None,
            forum_user=self.forum_user.to_dto() if self.forum_user else None,
        )
