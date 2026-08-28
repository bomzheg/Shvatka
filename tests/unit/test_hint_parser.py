import typing
from datetime import datetime, UTC
from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.types import Animation, Chat, Message, PhotoSize, Video

from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from tests.mocks.file_storage import MemoryFileStorage

AUTHOR = dto.Player(id=1, can_be_author=True, is_dummy=False)
PHOTO = {"photo": [PhotoSize(file_id="FILE_ID", file_unique_id="unique", width=1, height=1)]}
VIDEO = {"video": Video(file_id="FILE_ID", file_unique_id="unique", width=1, height=1, duration=1)}
ANIMATION = {
    "animation": Animation(
        file_id="FILE_ID", file_unique_id="unique", width=1, height=1, duration=1
    )
}
SPOILERABLE = [
    (PHOTO, hints.PhotoHint),
    (VIDEO, hints.VideoHint),
    (ANIMATION, hints.AnimationHint),
]
SpoilerHint: typing.TypeAlias = hints.PhotoHint | hints.VideoHint | hints.AnimationHint


@pytest.fixture
def hint_parser() -> HintParser:
    bot = AsyncMock(Bot)
    bot.download.return_value = BytesIO(b"12345")
    dao = AsyncMock(FileInfoDao)
    return HintParser(dao=dao, file_storage=MemoryFileStorage(), bot=bot)


def media_message(**kwargs) -> Message:
    return Message(
        message_id=1,
        date=datetime.now(tz=UTC),
        chat=Chat(id=1, type="private"),
        **kwargs,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(("media", "hint_type"), SPOILERABLE)
async def test_parse_media_with_spoiler(
    hint_parser: HintParser,
    media: dict[str, Any],
    hint_type: type[hints.BaseHint],
):
    hint = await hint_parser.parse(media_message(**media, has_media_spoiler=True), AUTHOR)

    assert isinstance(hint, hint_type)
    assert typing.cast(SpoilerHint, hint).has_spoiler is True


@pytest.mark.asyncio
@pytest.mark.parametrize(("media", "hint_type"), SPOILERABLE)
async def test_parse_media_without_spoiler(
    hint_parser: HintParser,
    media: dict[str, Any],
    hint_type: type[hints.BaseHint],
):
    hint = await hint_parser.parse(media_message(**media, caption="подпись"), AUTHOR)

    assert isinstance(hint, hint_type)
    parsed = typing.cast(SpoilerHint, hint)
    assert not parsed.has_spoiler
    assert parsed.caption == "подпись"
