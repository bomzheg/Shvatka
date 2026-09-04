from sqlalchemy import ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shvatka.infrastructure.db.models import Base


class LevelFile(Base):
    __tablename__ = "level_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level_id: Mapped[int] = mapped_column(ForeignKey("levels.id"))
    file_id: Mapped[int] = mapped_column(ForeignKey("files_info.id"))

    __table_args__ = (
        UniqueConstraint("level_id", "file_id"),
        Index("ix__level_files__file_id", "file_id"),
    )


class GameFile(Base):
    __tablename__ = "game_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    file_id: Mapped[int] = mapped_column(ForeignKey("files_info.id"))

    __table_args__ = (
        UniqueConstraint("game_id", "file_id"),
        Index("ix__game_files__file_id", "file_id"),
    )
