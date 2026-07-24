import tempfile
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pytest

from shvatka.common.config.models.main import FileStorageConfig
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import hints
from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.clients.file_storage import LocalFileStorage

CONTENT = b"\xff\xd8\xff\xe0" + b"\x00" * 1000
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class _UpsertRecordingDao:
    def __init__(self) -> None:
        self.upserted: hints.FileMeta | None = None

    async def upsert(self, file: hints.FileMeta, author: dto.Player) -> None:
        self.upserted = file

    async def update_file_id(self, guid: str, file_id: str) -> None:
        pass


class _StreamDrainingGateway(BotFileGateway):
    """Uses the real ``put``, but replaces the telegram upload with something
    that only drains the stream — which is all the real one does to it."""

    def __init__(self, storage: LocalFileStorage, dao: _UpsertRecordingDao) -> None:
        self.storage = storage
        self.dao = dao  # type: ignore[assignment]
        self.uploaded: bytes | None = None

    async def upload_to_tg(
        self, author: dto.Player, content: BinaryIO, file_meta: hints.FileMetaLightweight
    ) -> None:
        self.uploaded = content.read()


@pytest.mark.asyncio
async def test_put_stores_content_of_file_uploaded_to_tg():
    """Uploading to telegram must not eat the content before it is stored.

    A file with no file_id is first sent to telegram, which reads the whole
    stream; the storage must still receive the full content afterwards.
    """
    storage = LocalFileStorage(
        FileStorageConfig(
            path=Path(tempfile.mkdtemp()) / "files",
            mkdir=True,
            parents=True,
            exist_ok=True,
        )
    )
    dao = _UpsertRecordingDao()
    gateway = _StreamDrainingGateway(storage, dao)
    file_meta = hints.UploadedFileMeta(
        guid="1a5b0e0e-1d1e-4a1b-9c1d-0e1f2a3b4c5d",
        original_filename="screenshot",
        extension=".jpg",
        content_type=enums.HintType.photo,
    )

    await gateway.put(file_meta, BytesIO(CONTENT), author=None)

    assert gateway.uploaded == CONTENT
    saved = dao.upserted
    assert saved is not None
    assert (await storage.get(saved.file_content_link)).read() == CONTENT
    assert saved.sha256 != EMPTY_SHA256
    assert saved.mime_type != "application/x-empty"


@pytest.mark.asyncio
async def test_put_stores_content_of_file_already_in_tg():
    """A file that already has a file_id is not re-uploaded, and is stored as is."""
    storage = LocalFileStorage(
        FileStorageConfig(
            path=Path(tempfile.mkdtemp()) / "files",
            mkdir=True,
            parents=True,
            exist_ok=True,
        )
    )
    dao = _UpsertRecordingDao()
    gateway = _StreamDrainingGateway(storage, dao)
    file_meta = hints.UploadedFileMeta(
        guid="2b6c1f1f-2e2f-5b2c-0d2e-1f2a3b4c5d6e",
        original_filename="screenshot",
        extension=".jpg",
        content_type=enums.HintType.photo,
        file_id="already-in-telegram",
    )

    await gateway.put(file_meta, BytesIO(CONTENT), author=None)

    assert gateway.uploaded is None
    saved = dao.upserted
    assert saved is not None
    assert (await storage.get(saved.file_content_link)).read() == CONTENT
