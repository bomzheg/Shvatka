from __future__ import annotations

from dataclasses import dataclass

from shvatka.models import dto
from shvatka.models.enums.hint_type import HintType


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
class FileMeta:
    guid: str
    """GUID for filename in file storage, DB and in archive"""
    original_filename: str
    """Filename from user before renamed to guid"""
    extension: str
    """extension with leading dot: ".zip" ".tar.gz" etc"""
    tg_link: TgLink
    file_content_link: FileContentLink

    @property
    def local_file_name(self):
        return self.guid + (self.extension or "")

    @property
    def public_filename(self):
        return self.original_filename + (self.extension or "")


@dataclass
class SavedFileMeta(FileMeta):
    id: int
    author: dto.Player
