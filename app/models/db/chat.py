from sqlalchemy import Column, Text, BigInteger, Enum

from app.enums.chat_type import ChatType
from app.models.db.base import Base


class Chat(Base):
    __tablename__ = "chats"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(BigInteger, primary_key=True)
    tg_id = Column(BigInteger, unique=True)
    type = Column(Enum(ChatType))
    title = Column(Text, nullable=True)
    username = Column(Text, nullable=True)

    def __repr__(self):
        rez = (
            f"<Chat "
            f"ID={self.tg_id} "
            f"title={self.title} "
        )
        if self.username:
            rez += f"username=@{self.username}"
        return rez + ">"
