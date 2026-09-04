from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from shvatka.core.models import dto
from shvatka.core.models.enums.hint_type import HintType


@dataclass(frozen=True)
class FileUploadOptions:
    allow_conversion: bool = False
    """convert an unsupported image to a browser/Telegram-friendly format (JPEG)"""
    save_unsupported_as_is: bool = False
    """when conversion is not allowed, store the original bytes untouched instead
    of rejecting the upload"""


DEFAULT_UPLOAD_OPTIONS = FileUploadOptions()
"""shared immutable default for callers that don't set an explicit upload policy"""


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


@dataclass(frozen=True)
class StoredFile:
    link: FileContentLink
    modified_at: datetime


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
    file_id: str | None = field(kw_only=True, default=None)
    """telegram file_id, or ``None`` until the file is uploaded to telegram"""
    sha256: str | None = field(kw_only=True, default=None)
    """SHA-256 hex digest of file content for deduplication"""
    mime_type: str | None = field(kw_only=True, default=None)
    """Actual MIME type detected from file content (e.g. image/jpeg)"""

    @property
    def local_file_name(self):
        return self.guid + (self.extension or "")

    @property
    def public_filename(self):
        return self.original_filename + (self.extension or "")

    @property
    def tg_link(self) -> TgLink | None:
        if self.file_id is None or self.content_type is None:
            return None
        return TgLink(file_id=self.file_id, content_type=self.content_type)


@dataclass
class StoredFileMeta(FileMetaLightweight):
    file_content_link: FileContentLink


@dataclass
class UploadedFileMeta(FileMetaLightweight):
    pass


@dataclass
class FileMeta(StoredFileMeta):
    pass


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
