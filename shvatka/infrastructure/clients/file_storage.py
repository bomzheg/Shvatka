import asyncio
import hashlib
import logging
import mimetypes
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import magic

from shvatka.common.config.models.main import FileStorageConfig
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models.dto import hints
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.exceptions import UnsupportedFileFormat
from shvatka.infrastructure.clients.image_converter import (
    JPEG_EXTENSION,
    convert_heic_to_jpeg,
    is_heic,
)

logger = logging.getLogger(__name__)


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


EMPTY_CONTENT_SHA256 = compute_sha256(b"")
"""sha256 of no content at all — marks a file that was saved empty"""


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

    async def put(
        self,
        file_meta: hints.UploadedFileMeta,
        content: BinaryIO,
        options: hints.FileUploadOptions = hints.DEFAULT_UPLOAD_OPTIONS,
    ) -> hints.FileMeta:
        # sniffing the type, hashing the bytes and transcoding an image are all
        # cpu over the whole upload, and a hint can be tens of megabytes. one
        # hop into a thread for the lot of them rather than one hop each
        data, mime_type, extension, sha256 = await asyncio.to_thread(
            self._inspect, file_meta, content.read(), options
        )
        local_name = file_meta.guid + extension
        file_content_link = await self.put_content(local_name, BytesIO(data))
        return hints.FileMeta(
            file_content_link=file_content_link,
            guid=file_meta.guid,
            original_filename=file_meta.original_filename,
            extension=extension,
            file_id=file_meta.file_id,
            content_type=file_meta.content_type,
            sha256=sha256,
            mime_type=mime_type,
        )

    def _inspect(
        self,
        file_meta: hints.UploadedFileMeta,
        data: bytes,
        options: hints.FileUploadOptions,
    ) -> tuple[bytes, str, str, str]:
        mime_type = detect_mime_type(data)
        extension = file_meta.extension or extension_from_mime(mime_type)
        if is_heic(mime_type):
            data, mime_type, extension = self._handle_unsupported(
                data, mime_type, extension, options
            )
        return data, mime_type, extension, compute_sha256(data)

    def _handle_unsupported(
        self,
        data: bytes,
        mime_type: str,
        extension: str,
        options: hints.FileUploadOptions,
    ) -> tuple[bytes, str, str]:
        if options.allow_conversion:
            converted = convert_heic_to_jpeg(data)
            if converted is not data:
                return converted, detect_mime_type(converted), JPEG_EXTENSION
            if options.save_unsupported_as_is:
                return data, mime_type, extension
            raise UnsupportedFileFormat(
                text=f"can't convert unsupported image of type {mime_type}"
            )
        if options.save_unsupported_as_is:
            return data, mime_type, extension
        raise UnsupportedFileFormat(text=f"unsupported image of type {mime_type}")

    async def put_content(self, local_file_name: str, content: BinaryIO) -> hints.FileContentLink:
        result_path = self.path / local_file_name
        await asyncio.to_thread(result_path.write_bytes, content.read())
        return hints.FileContentLink(file_path=str(result_path))

    async def get(self, file_link: hints.FileContentLink) -> BinaryIO:
        # a hint is read off disk to be sent whenever telegram has forgotten its
        # file_id, which during a game is once per team
        return BytesIO(await asyncio.to_thread(Path(file_link.file_path).read_bytes))

    async def exists(self, file_link: hints.FileContentLink) -> bool:
        return await asyncio.to_thread(Path(file_link.file_path).is_file)

    async def delete(self, file_link: hints.FileContentLink) -> None:
        await asyncio.to_thread(Path(file_link.file_path).unlink, missing_ok=True)

    async def list_files(self) -> list[hints.StoredFile]:
        return await asyncio.to_thread(self._list_files)

    def _list_files(self) -> list[hints.StoredFile]:
        return [
            hints.StoredFile(
                link=hints.FileContentLink(file_path=str(path)),
                modified_at=datetime.fromtimestamp(path.stat().st_mtime, tz=tz_utc),
            )
            for path in self.path.iterdir()
            if path.is_file()
        ]
