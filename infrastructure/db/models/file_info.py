from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from infrastructure.db.models import Base
from shvatka.models import dto
from shvatka.models.dto.scn import SavedFileMeta, TgLink, FileContentLink
from shvatka.models.dto.scn.file_content import VerifiableFileMeta
from shvatka.models.enums.hint_type import HintType


class FileInfo(Base):
    __tablename__ = "files_info"
    __mapper_args__ = {"eager_defaults": True}
    id = Column(Integer, primary_key=True)
    file_path = Column(Text)
    guid = Column(Text, unique=True)
    original_filename = Column(Text)
    extension = Column(Text)
    file_id = Column(Text)
    content_type = Column(Text)
    author_id = Column(ForeignKey("players.id"), nullable=False)
    author = relationship(
        "Player",
        foreign_keys=author_id,
        back_populates="my_files",
    )

    def to_dto(self, author: dto.Player) -> SavedFileMeta:
        return SavedFileMeta(
            id=self.id,
            guid=self.guid,
            original_filename=self.original_filename,
            extension=self.extension,
            author=author,
            author_id=self.author_id,
            tg_link=TgLink(file_id=self.file_id, content_type=HintType[self.content_type]),
            file_content_link=FileContentLink(file_path=self.file_path),
        )

    def to_short_dto(self) -> VerifiableFileMeta:
        return VerifiableFileMeta(
            guid=self.guid,
            original_filename=self.original_filename,
            author_id=self.author_id,
            extension=self.extension,
            tg_link=TgLink(file_id=self.file_id, content_type=HintType[self.content_type]),
            file_content_link=FileContentLink(file_path=self.file_path),
        )