from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.types import Chat, Message, PhotoSize

from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from tests.mocks.file_storage import MemoryFileStorage

AUTHOR = dto.Player(id=1, can_be_author=True, is_dummy=False)


@pytest.fixture
def hint_parser() -> HintParser:
    bot = AsyncMock(Bot)
    bot.download.return_value = BytesIO(b"12345")
    dao = AsyncMock(FileInfoDao)
    return HintParser(dao=dao, file_storage=MemoryFileStorage(), bot=bot)


def photo_message(**kwargs) -> Message:
    return Message(
        message_id=1,
        date=datetime.now(tz=timezone.utc),
        chat=Chat(id=1, type="private"),
        photo=[PhotoSize(file_id="FILE_ID", file_unique_id="unique", width=1, height=1)],
        **kwargs,
    )


@pytest.mark.asyncio
async def test_parse_photo_with_spoiler(hint_parser: HintParser):
    hint = await hint_parser.parse(photo_message(has_media_spoiler=True), AUTHOR)

    assert isinstance(hint, hints.PhotoHint)
    assert hint.has_spoiler is True


@pytest.mark.asyncio
async def test_parse_photo_without_spoiler(hint_parser: HintParser):
    hint = await hint_parser.parse(photo_message(caption="подпись"), AUTHOR)

    assert isinstance(hint, hints.PhotoHint)
    assert not hint.has_spoiler
    assert hint.caption == "подпись"
