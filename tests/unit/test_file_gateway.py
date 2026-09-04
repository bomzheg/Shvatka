import tempfile
import typing
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from unittest import mock

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import SendPhoto

from shvatka.common.config.models.main import FileStorageConfig
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import hints
from shvatka.core.utils.exceptions import FileRejectedByTelegram
from shvatka.infrastructure.clients.file_gateway import BotFileGateway
from shvatka.infrastructure.clients.file_storage import LocalFileStorage

CONTENT = b"\xff\xd8\xff\xe0" + b"\x00" * 1000
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
CHAT_ID = 42
AUTHOR = dto.Player(id=1, can_be_author=True, is_dummy=False, username="author")


class _UpsertRecordingDao:
    def __init__(self) -> None:
        self.upserted: hints.FileMeta | None = None
        self.file_ids: dict[str, str] = {}

    async def upsert(self, file: hints.FileMeta, author: dto.Player) -> None:
        self.upserted = file

    async def update_file_id(self, guid: str, file_id: str) -> None:
        # the real one is an UPDATE: a guid with no row yet is a no-op
        if self.upserted is not None and self.upserted.guid == guid:
            self.file_ids[guid] = file_id


class _StreamDrainingGateway(BotFileGateway):
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


def _refusing_bot(error: TelegramAPIError) -> Bot:
    bot = Bot(token="42:TESTTESTTESTTESTTESTTESTTESTTESTTES", session=mock.AsyncMock(BaseSession))
    typing.cast(mock.MagicMock, bot.session).side_effect = error
    return bot


@pytest.mark.asyncio
async def test_telegram_refusal_is_translated_to_a_domain_error():
    error = TelegramAPIError(message="Request Entity Too Large", method=SendPhoto)
    gateway = BotFileGateway(
        file_storage=None,
        dao=_UpsertRecordingDao(),
        bot=_refusing_bot(error),
        tech_chat_id=CHAT_ID,
    )
    file_meta = hints.UploadedFileMeta(
        guid="3c7d2020-3f30-6c3d-1e3f-2a3b4c5d6e7f",
        original_filename="huge",
        extension=".jpg",
        content_type=enums.HintType.photo,
    )

    with pytest.raises(FileRejectedByTelegram) as exc_info:
        await gateway.upload_to_tg(AUTHOR, BytesIO(CONTENT), file_meta)

    rejected = exc_info.value
    assert rejected.guid == file_meta.guid
    assert rejected.filename == "huge.jpg"
    # the author is told which file and what telegram said about it
    assert "huge.jpg" in str(rejected.notify_user)
    assert "Request Entity Too Large" in str(rejected.notify_user)


class _FileIdKeepingGateway(BotFileGateway):
    def __init__(self, storage: LocalFileStorage, dao: _UpsertRecordingDao) -> None:
        self.storage = storage
        self.dao = dao  # type: ignore[assignment]

    async def upload_to_tg(
        self, author: dto.Player, content: BinaryIO, file_meta: hints.FileMetaLightweight
    ) -> None:
        await self.dao.update_file_id(file_meta.guid, "from-telegram")


@pytest.mark.asyncio
async def test_put_keeps_the_file_id_telegram_answered_with():
    storage = LocalFileStorage(
        FileStorageConfig(
            path=Path(tempfile.mkdtemp()) / "files",
            mkdir=True,
            parents=True,
            exist_ok=True,
        )
    )
    dao = _UpsertRecordingDao()
    gateway = _FileIdKeepingGateway(storage, dao)
    file_meta = hints.UploadedFileMeta(
        guid="4d8e3131-4041-7d4e-2f40-3b4c5d6e7f80",
        original_filename="screenshot",
        extension=".jpg",
        content_type=enums.HintType.photo,
    )

    await gateway.put(file_meta, BytesIO(CONTENT), author=AUTHOR)

    assert dao.file_ids == {file_meta.guid: "from-telegram"}
