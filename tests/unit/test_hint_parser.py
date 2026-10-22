import typing
from datetime import UTC, datetime
from io import BytesIO
from typing import Any
from unittest.mock import ANY, AsyncMock

import pytest
from aiogram import Bot, types
from aiogram.types import Animation, Chat, Message, PhotoSize, Video

from shvatka.core.models import dto, enums
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


@pytest.mark.asyncio
async def test_parse_rich_message(hint_parser: HintParser):
    """An incoming rich message is stored as the markup it was written in."""
    rich_message = types.RichMessage(
        blocks=[
            types.RichBlockSectionHeading(text="Загадка", size=1),
            types.RichBlockParagraph(text=["найди ", types.RichTextBold(text="дом")]),
        ]
    )

    hint = await hint_parser.parse(media_message(rich_message=rich_message), AUTHOR)

    assert isinstance(hint, hints.RichHint)
    assert hint.text == "<h1>Загадка</h1><p>найди <b>дом</b></p>"
    assert hint.format == enums.RichFormat.html
    assert hint.media == []
    assert hint.get_guids() == []


@pytest.mark.asyncio
async def test_parse_rich_message_saves_its_media(hint_parser: HintParser):
    """Every file the message embeds is stored, and the markup keeps pointing
    at it by the media id."""
    rich_message = types.RichMessage(
        blocks=[
            types.RichBlockPhoto(
                photo=[PhotoSize(file_id="PHOTO_ID", file_unique_id="u", width=1, height=1)]
            )
        ]
    )

    hint = await hint_parser.parse(media_message(rich_message=rich_message), AUTHOR)

    assert isinstance(hint, hints.RichHint)
    assert hint.text == '<img src="tg://photo?id=media1"/>'
    assert [media.id for media in hint.media] == ["media1"]
    # the file is saved under a guid of its own, and the hint owns it
    assert hint.get_guids() == [hint.media[0].file_guid]
    download = typing.cast(AsyncMock, hint_parser.bot.download)
    download.assert_awaited_once_with("PHOTO_ID", ANY)
