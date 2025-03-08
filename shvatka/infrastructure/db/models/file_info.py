from sqlalchemy import Integer, Text, ForeignKey
from sqlalchemy.orm import relationship, mapped_column

from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.core.models.enums.hint_type import HintType
from shvatka.infrastructure.db.models import Base


class FileInfo(Base):
    __tablename__ = "files_info"
    __mapper_args__ = {"eager_defaults": True}
    id = mapped_column(Integer, primary_key=True)
    file_path = mapped_column(Text)
    guid = mapped_column(Text, unique=True)
    original_filename = mapped_column(Text)
    extension = mapped_column(Text)
    file_id = mapped_column(Text)
    content_type = mapped_column(Text)
    author_id = mapped_column(ForeignKey("players.id"), nullable=False)
    author = relationship(
        "Player",
        foreign_keys=author_id,
        back_populates="my_files",
    )

    def to_dto(self, author: dto.Player) -> hints.SavedFileMeta:
        content_type = HintType[self.content_type]
        return hints.SavedFileMeta(
            id=self.id,
            guid=self.guid,
            original_filename=self.original_filename,
            extension=self.extension,
            author=author,
            author_id=self.author_id,
            tg_link=hints.TgLink(file_id=self.file_id, content_type=content_type),
            content_type=content_type,
            file_content_link=hints.FileContentLink(file_path=self.file_path),
        )

    def to_short_dto(self) -> hints.VerifiableFileMeta:
        content_type = HintType[self.content_type]
        return hints.VerifiableFileMeta(
            guid=self.guid,
            original_filename=self.original_filename,
            author_id=self.author_id,
            extension=self.extension,
            tg_link=hints.TgLink(file_id=self.file_id, content_type=content_type),
            content_type=content_type,
            file_content_link=hints.FileContentLink(file_path=self.file_path),
        )
