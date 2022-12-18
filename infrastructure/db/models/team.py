from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from infrastructure.db.models import Base
from shvatka.models import dto


class Team(Base):
    __tablename__ = "teams"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    chat_id = Column(ForeignKey("chats.id"), unique=True)
    chat = relationship(
        "Chat",
        foreign_keys=chat_id,
        back_populates="team",
    )
    captain_id = Column(ForeignKey("players.id"))
    captain = relationship(
        "Player",
        foreign_keys=captain_id,
        back_populates="captain_by_team",
    )
    description = Column(Text)

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

    def to_dto(self, chat: dto.Chat) -> dto.Team:
        return dto.Team(
            id=self.id,
            chat=chat,
            name=self.name,
            description=self.description,
            captain=self.captain.to_dto(
                user=self.captain.user.to_dto(),
            ),
        )
