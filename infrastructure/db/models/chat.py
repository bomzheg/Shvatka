from sqlalchemy import Text, BigInteger, Enum
from sqlalchemy.orm import relationship, mapped_column

from infrastructure.db.models.base import Base
from shvatka.models import dto
from shvatka.models.enums.chat_type import ChatType


class Chat(Base):
    __tablename__ = "chats"
    __mapper_args__ = {"eager_defaults": True}
    id = mapped_column(BigInteger, primary_key=True)
    tg_id = mapped_column(BigInteger, unique=True)
    type = mapped_column(Enum(ChatType))
    title = mapped_column(Text, nullable=True)
    username = mapped_column(Text, nullable=True)

    team = relationship(
        "Team",
        back_populates="chat",
        foreign_keys="Team.chat_id",
    )

    def __repr__(self):
        rez = f"<Chat ID={self.tg_id} title={self.title} "
        if self.username:
            rez += f"username=@{self.username}"
        return rez + ">"

    def to_dto(self) -> dto.Chat:
        return dto.Chat(
            tg_id=self.tg_id,
            db_id=self.id,
            title=self.title,
            type=self.type,
            username=self.username,
        )
