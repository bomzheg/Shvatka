import hashlib
import logging
import mimetypes
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import magic

from shvatka.common.config.models.main import FileStorageConfig
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models.dto import hints
from shvatka.infrastructure.clients.image_converter import (
    JPEG_EXTENSION,
    convert_heic_to_jpeg,
    is_heic,
)

logger = logging.getLogger(__name__)


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def detect_mime_type(data: bytes) -> str:
    return magic.from_buffer(data, mime=True)


def extension_from_mime(mime_type: str) -> str:
    ext = mimetypes.guess_extension(mime_type)
    if ext is None:
        return ""
    # mimetypes may return .jpe for image/jpeg — normalise common cases
    _normalise = {".jpe": ".jpg", ".jfif": ".jpg"}
    return _normalise.get(ext, ext)


class LocalFileStorage(FileStorage):
    def __init__(self, config: FileStorageConfig) -> None:
        self.path = config.path
        logger.info("as local file storage use '%s'", self.path)
        if config.mkdir:
            self.path.mkdir(exist_ok=config.exist_ok, parents=config.parents)

    async def put(self, file_meta: hints.UploadedFileMeta, content: BinaryIO) -> hints.FileMeta:
        data = content.read()
        mime_type = detect_mime_type(data)
        extension = file_meta.extension or extension_from_mime(mime_type)
        if is_heic(mime_type):
            # HEIC/HEIF can't be shown in browsers and isn't supported by Telegram,
            # so transcode it to JPEG before storing (see issue #289).
            converted = convert_heic_to_jpeg(data)
            if converted is not data:
                data = converted
                mime_type = detect_mime_type(data)
                extension = JPEG_EXTENSION
        sha256 = compute_sha256(data)
        local_name = file_meta.guid + extension
        file_content_link = await self.put_content(local_name, BytesIO(data))
        return hints.FileMeta(
            file_content_link=file_content_link,
            guid=file_meta.guid,
            original_filename=file_meta.original_filename,
            extension=extension,
            tg_link=file_meta.tg_link,  # type: ignore
            content_type=file_meta.content_type,
            sha256=sha256,
            mime_type=mime_type,
        )

    async def put_content(self, local_file_name: str, content: BinaryIO) -> hints.FileContentLink:
        result_path = self.path / local_file_name
        with result_path.open("wb") as f:
            f.write(content.read())
        return hints.FileContentLink(file_path=str(result_path))

    async def get(self, file_link: hints.FileContentLink) -> BinaryIO:
        with Path(file_link.file_path).open("rb") as f:  # noqa: ASYNC101
            result = BytesIO(f.read())
        return result

    async def exists(self, file_link: hints.FileContentLink) -> bool:
        return Path(file_link.file_path).is_file()
