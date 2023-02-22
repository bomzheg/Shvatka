from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped

from infrastructure.db.models import Base
from shvatka.models import dto


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
    )
    captain_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    captain = relationship(
        "Player",
        foreign_keys=captain_id,
        back_populates="captain_by_team",
    )
    description: Mapped[str]

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

    def to_dto(self, chat: dto.Chat | None) -> dto.Team:
        return dto.Team(
            id=self.id,
            chat=chat,
            name=self.name,
            is_dummy=self.is_dummy,
            description=self.description,
            captain=self.captain.to_dto_user_prefetched(),
        )

    def to_dto_chat_prefetched(self) -> dto.Team:
        return self.to_dto(self.chat.to_dto() if self.chat else None)
