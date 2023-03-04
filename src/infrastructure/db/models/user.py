from sqlalchemy import Text, BigInteger, Boolean, ForeignKey
from sqlalchemy.orm import relationship, mapped_column

from src.infrastructure.db.models.base import Base
from src.core.models import dto


class User(Base):
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}
    id = mapped_column(BigInteger, primary_key=True)
    tg_id = mapped_column(BigInteger, unique=True, nullable=False)
    first_name = mapped_column(Text, nullable=True)
    last_name = mapped_column(Text, nullable=True)
    username = mapped_column(Text, nullable=True)
    hashed_password = mapped_column(Text, nullable=True)
    is_bot = mapped_column(Boolean, default=False)
    player_id = mapped_column(ForeignKey("players.id"), unique=True)

    player = relationship(
        "Player",
        back_populates="user",
        foreign_keys=player_id,
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
        )
