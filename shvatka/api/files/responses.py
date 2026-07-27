from dataclasses import dataclass

from shvatka.core.models import enums
from shvatka.core.models.dto import hints


@dataclass
class GameFile:
    guid: str
    original_filename: str
    extension: str
    content_type: enums.HintType | None
    mime_type: str | None

    @classmethod
    def from_core(cls, core: hints.FileMeta) -> "GameFile":
        return cls(
            guid=core.guid,
            original_filename=core.original_filename,
            extension=core.extension,
            content_type=core.content_type,
            mime_type=core.mime_type,
        )


@dataclass
class UploadedFile:
    guid: str
    original_filename: str
    extension: str
    content_type: enums.HintType | None
    mime_type: str | None

    @classmethod
    def from_core(cls, core: hints.SavedFileMeta) -> "UploadedFile":
        return cls(
            guid=core.guid,
            original_filename=core.original_filename,
            extension=core.extension,
            content_type=core.content_type,
            mime_type=core.mime_type,
        )
