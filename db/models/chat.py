from sqlalchemy import Column, Text, BigInteger, Enum
from sqlalchemy.orm import relationship

from db.models.base import Base
from shvatka.models.enums.chat_type import ChatType


class Chat(Base):
    __tablename__ = "chats"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(BigInteger, primary_key=True)
    tg_id = Column(BigInteger, unique=True)
    type = Column(Enum(ChatType))
    title = Column(Text, nullable=True)
    username = Column(Text, nullable=True)

    team = relationship(
        "Team",
        back_populates="chat",
        foreign_keys="Team.chat_id",
    )

    def __repr__(self):
        rez = (
            f"<Chat "
            f"ID={self.tg_id} "
            f"title={self.title} "
        )
        if self.username:
            rez += f"username=@{self.username}"
        return rez + ">"
