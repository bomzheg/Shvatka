from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from db.models import Base
from shvatka.models import dto
from shvatka.models.dto.scn import SavedFileContent, TgLink, FileContentLink
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

    def to_dto(self, author: dto.Player) -> SavedFileContent:
        return SavedFileContent(
            id=self.id,
            guid=self.guid,
            original_filename=self.original_filename,
            extension=self.extension,
            author=author,
            tg_link=TgLink(file_id=self.file_id, content_type=HintType[self.content_type]),
            file_content_link=FileContentLink(file_path=self.file_path),
        )
