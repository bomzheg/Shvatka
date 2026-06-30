from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shvatka.infrastructure.db.models import Base


class LevelFile(Base):
    """m2m relation of which files a level actually references.

    Kept in sync with the level scenario: a row exists exactly while the file is
    used by the level (added when referenced, removed when no longer referenced).
    It is only for a quick inspection of what a level contains.
    """

    __tablename__ = "level_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level_id: Mapped[int] = mapped_column(ForeignKey("levels.id"))
    file_id: Mapped[int] = mapped_column(ForeignKey("files_info.id"))

    __table_args__ = (UniqueConstraint("level_id", "file_id"),)


class GameFile(Base):
    """m2m relation of which files CAN be used in a game.

    Mostly used by the UI constructor to choose an already uploaded file. Rows are
    only added (never removed on unlink): a file becomes available to a game when a
    level referencing it is linked, when a file is added to a linked level, or when
    a file is uploaded directly for the game.
    """

    __tablename__ = "game_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"))
    file_id: Mapped[int] = mapped_column(ForeignKey("files_info.id"))

    __table_args__ = (UniqueConstraint("game_id", "file_id"),)
