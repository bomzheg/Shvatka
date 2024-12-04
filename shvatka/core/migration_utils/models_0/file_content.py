from __future__ import annotations

from dataclasses import dataclass, field

from shvatka.core.models import dto
from shvatka.core.models.enums.hint_type import HintType


@dataclass
class TgLink:
    file_id: str
    """telegram file_id"""
    content_type: HintType
    """type of content"""


@dataclass
class FileContentLink:
    file_path: str
    """path to file in file system"""


@dataclass
class FileMetaLightweight:
    guid: str
    """GUID for filename in file storage, DB and in archive"""
    original_filename: str
    """Filename from user before renamed to guid"""
    extension: str
    """extension with leading dot: ".zip" ".tar.gz" etc"""
    content_type: HintType | None = field(kw_only=True, default=None)
    """type of content"""

    @property
    def local_file_name(self):
        return self.guid + (self.extension or "")

    @property
    def public_filename(self):
        return self.original_filename + (self.extension or "")


@dataclass
class StoredFileMeta(FileMetaLightweight):
    file_content_link: FileContentLink


@dataclass
class UploadedFileMeta(FileMetaLightweight):
    tg_link: TgLink | None = None


@dataclass
class FileMeta(StoredFileMeta):
    tg_link: TgLink


@dataclass
class VerifiableFileMeta(FileMeta):
    author_id: int


@dataclass
class SavedFileMeta(VerifiableFileMeta):
    id: int
    author: dto.Player


@dataclass
class ParsedTgLink(TgLink):
    filename: str | None = None
