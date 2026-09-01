from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shvatka.core.models import dto
from shvatka.infrastructure.db.models import Base, Player


class Team(Base):
    __tablename__ = "teams"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    is_dummy: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="f")
    chat = relationship(
        "Chat",
        foreign_keys="Chat.team_id",
        back_populates="team",
        uselist=False,
    )
    forum_team = relationship(
        "ForumTeam",
        foreign_keys="ForumTeam.team_id",
        back_populates="team",
        uselist=False,
    )
    captain_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    captain: Mapped[Player | None] = relationship(
        "Player",
        foreign_keys=captain_id,
        back_populates="captain_by_team",
    )
    description: Mapped[str | None]

    completed_levels = relationship(
        "LevelTime",
        back_populates="team",
        foreign_keys="LevelTime.team_id",
    )
    typed_keys = relationship(
        "KeyTime",
        back_populates="team",
        foreign_keys="KeyTime.team_id",
    )
    played_games = relationship(
        "Waiver",
        back_populates="team",
        foreign_keys="Waiver.team_id",
    )
    players = relationship(
        "TeamPlayer",
        back_populates="team",
        foreign_keys="TeamPlayer.team_id",
    )

    __table_args__ = (Index("ix__teams__captain_id", "captain_id"),)

    def to_dto(
        self,
        chat: dto.Chat | None = None,
        forum_team: dto.ForumTeam | None = None,
    ) -> dto.Team:
        """DTO of a team without its captain: `captain_id` comes from the row."""
        return dto.Team(
            id=self.id,
            chat=chat,
            forum_team=forum_team,
            name=self.name,
            is_dummy=self.is_dummy,
            description=self.description,
            captain_id=self.captain_id,
        )

    def to_dto_with_captain(
        self,
        chat: dto.Chat | None = None,
        forum_team: dto.ForumTeam | None = None,
        captain: dto.Player | None = None,
    ) -> dto.TeamWithCaptain:
        """Only for queries that eagerly loaded `captain` — it is read here."""
        if not captain and self.captain:
            captain = self.captain.to_dto_user_prefetched()

        return dto.TeamWithCaptain(
            id=self.id,
            chat=chat,
            forum_team=forum_team,
            name=self.name,
            is_dummy=self.is_dummy,
            description=self.description,
            captain=captain,
            captain_id=self.captain_id,
        )

    def to_dto_chat_prefetched(self) -> dto.Team:
        """Chat and forum team prefetched, captain left unloaded."""
        return self.to_dto(
            chat=self.chat.to_dto() if self.chat else None,
            forum_team=self.forum_team.to_dto() if self.forum_team else None,
        )

    def to_dto_with_captain_prefetched(self) -> dto.TeamWithCaptain:
        return self.to_dto_with_captain(
            chat=self.chat.to_dto() if self.chat else None,
            forum_team=self.forum_team.to_dto() if self.forum_team else None,
        )
