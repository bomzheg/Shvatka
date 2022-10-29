from sqlalchemy import Column, Text, BigInteger, Boolean
from sqlalchemy.orm import relationship

from db.models.base import Base
from shvatka.models import dto


class User(Base):
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(BigInteger, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=True)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    username = Column(Text, nullable=True)
    hashed_password = Column(Text, nullable=True)
    is_bot = Column(Boolean, default=False)

    player = relationship(
        "Player",
        back_populates="user",
        foreign_keys="Player.user_id",
        uselist=False,
    )

    def __repr__(self):
        rez = (
            f"<User "
            f"id={self.id} "
            f"tg_id={self.tg_id} "
            f"name={self.first_name} {self.last_name} "
        )
        if self.username:
            rez += f"username=@{self.username}"
        return rez + ">"

    def to_dto(self) -> dto.User:
        return dto.User(
            db_id=self.id,
            tg_id=self.tg_id,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            is_bot=self.is_bot,
            hashed_password=self.hashed_password
        )
