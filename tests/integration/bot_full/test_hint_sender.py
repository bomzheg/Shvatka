import typing
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Chat, Message, PhotoSize
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from aiogram.methods import (
    SendPhoto,
    TelegramMethod,
    SendAudio,
    SendVideo,
    SendDocument,
    SendAnimation,
    SendVoice,
    SendVideoNote,
    SendSticker,
)
from aiogram.methods.base import TelegramType

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import hints
from shvatka.core.models.dto.hints import TextHint, GPSHint, PhotoHint, BaseHint
from shvatka.core.models.dto.hints import (
    VenueHint,
    AudioHint,
    VideoHint,
    DocumentHint,
    AnimationHint,
    VoiceHint,
    VideoNoteHint,
    StickerHint,
)
from shvatka.infrastructure.db.dao import FileInfoDao
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.config.models.main import TgBotConfig
from shvatka.tgbot.views.hint_factory.hint_content_resolver import HintContentResolver
from shvatka.tgbot.views.hint_sender import HintSender
from tests.fixtures.file_storage import FILE_ID, CHAT_ID, FILE_META
from tests.fixtures.scn_fixtures import GUID

BAD_REQUEST_DESC = (
    "Bad Request: wrong remote file identifier specified: Wrong padding in the string"
)
PARAMETERS = [
    (SendPhoto, PhotoHint(file_guid=GUID), "sendPhoto", "photo"),
    (SendAudio, AudioHint(file_guid=GUID), "sendAudio", "audio"),
    (SendVideo, VideoHint(file_guid=GUID), "sendVideo", "video"),
    (SendDocument, DocumentHint(file_guid=GUID), "sendDocument", "document"),
    (SendAnimation, AnimationHint(file_guid=GUID), "sendAnimation", "animation"),
    (SendVoice, VoiceHint(file_guid=GUID), "sendVoice", "voice"),
    (SendVideoNote, VideoNoteHint(file_guid=GUID), "sendVideoNote", "video_note"),
    (SendSticker, StickerHint(file_guid=GUID), "sendSticker", "sticker"),
]


@pytest_asyncio.fixture
async def hint_sender(
    dao: HolderDao,
    file_storage: FileStorage,
    bot_session: BaseSession,
    bot_config: TgBotConfig,
    dishka: AsyncContainer,
):
    bot = Bot(token=bot_config.bot.token, session=bot_session)
    pool = await dishka.get(async_sessionmaker[AsyncSession])
    async with pool() as session:
        yield HintSender(
            bot=bot,
            resolver=HintContentResolver(dao=dao.file_info, file_storage=file_storage),
            file_info_dao=FileInfoDao(session),
        )


@pytest.mark.asyncio
async def test_send_text(hint_sender: HintSender, bot_session: BaseSession):
    hint = TextHint(text="Привет")

    await hint_sender.send_hint(hint, CHAT_ID)

    session = typing.cast(MagicMock, bot_session)
    assert 1 == session.call_count
    call = session.mock_calls.pop()
    request = call.args[1]
    assert request.__api_method__ == "sendMessage"
    assert request.text == hint.text


@pytest.mark.asyncio
async def test_send_location(hint_sender: HintSender, bot_session: BaseSession):
    hint = GPSHint(longitude=55.59, latitude=37.88)

    await hint_sender.send_hint(hint, CHAT_ID)

    session = typing.cast(MagicMock, bot_session)
    assert 1 == session.call_count
    call = session.mock_calls.pop()
    request = call.args[1]

    assert request.__api_method__ == "sendLocation"
    assert request.longitude == hint.longitude
    assert request.latitude == hint.latitude


@pytest.mark.asyncio
async def test_send_venue(hint_sender: HintSender, bot_session: BaseSession):
    hint = VenueHint(longitude=55.59, latitude=37.88, title="awesome cafe", address="Ленина, 1")

    await hint_sender.send_hint(hint, CHAT_ID)

    session = typing.cast(MagicMock, bot_session)
    assert 1 == session.call_count
    call = session.mock_calls.pop()
    request = call.args[1]
    assert request.__api_method__ == "sendVenue"
    assert request.longitude == hint.longitude
    assert request.latitude == hint.latitude
    assert request.title == hint.title
    assert request.address == hint.address
    assert request.foursquare_id == hint.foursquare_id
    assert request.foursquare_type == hint.foursquare_type


@pytest.mark.asyncio
@pytest.mark.parametrize(("tg_method", "hint", "method_name", "content_type"), PARAMETERS)
async def test_send_photo_by_id(
    hint_sender: HintSender,
    harry: dto.Player,
    hint: BaseHint,
    tg_method: type[TelegramMethod[TelegramType]],
    method_name: str,
    content_type: str,
    bot_session: BaseSession,
):
    await hint_sender.resolver.dao.upsert(file=FILE_META, author=harry)
    await hint_sender.resolver.dao.commit()

    await hint_sender.send_hint(hint, CHAT_ID)

    session = typing.cast(MagicMock, bot_session)
    assert 1 == session.call_count
    call = session.mock_calls.pop()
    request = call.args[1]
    assert request.__api_method__ == method_name
    assert getattr(request, content_type) == FILE_ID


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tg_method", "hint", "method_name", "content_type"), tuple(PARAMETERS[:-1])
)  # we don't send sticker by content
async def test_send_photo_by_content(
    hint_sender: HintSender,
    harry: dto.Player,
    hint: BaseHint,
    tg_method: TelegramMethod[TelegramType],
    method_name: str,
    content_type: str,
    bot_session: BaseSession,
):
    await hint_sender.resolver.storage.put_content(FILE_META.local_file_name, BytesIO(b"12345"))
    await hint_sender.resolver.dao.upsert(file=FILE_META, author=harry)
    await hint_sender.resolver.dao.commit()
    session = typing.cast(MagicMock, bot_session)
    session.side_effect = [
        TelegramAPIError(message="", method=tg_method),
        {},
    ]

    await hint_sender.send_hint(hint, CHAT_ID)

    assert 2 == session.call_count

    call = session.mock_calls.pop()
    request = call.args[1]
    assert request.__api_method__ == method_name
    assert getattr(request, content_type) is not None

    call = session.mock_calls.pop()
    request = call.args[1]
    assert request.__api_method__ == method_name
    assert getattr(request, content_type) == FILE_ID


@pytest.mark.asyncio
async def test_send_by_content_when_file_id_missing(
    hint_sender: HintSender,
    harry: dto.Player,
    bot_session: BaseSession,
):
    file_meta = hints.FileMeta(
        guid=GUID,
        tg_link=hints.TgLink(file_id=None, content_type=enums.HintType.photo),
        extension=".jpg",
        file_content_link=hints.FileContentLink(file_path=GUID + ".jpg"),
        original_filename="файло",
    )
    await hint_sender.resolver.storage.put_content(file_meta.local_file_name, BytesIO(b"12345"))
    await hint_sender.resolver.dao.upsert(file=file_meta, author=harry)
    await hint_sender.resolver.dao.commit()
    session = typing.cast(MagicMock, bot_session)
    session.side_effect = [{}]

    await hint_sender.send_hint(PhotoHint(file_guid=GUID), CHAT_ID)

    # no attempt to send by (missing) file_id, straight to content
    assert 1 == session.call_count
    call = session.mock_calls.pop()
    request = call.args[1]
    assert request.__api_method__ == "sendPhoto"
    assert request.photo is not None


@pytest.mark.asyncio
async def test_renew_file_id_after_send_by_content(
    hint_sender: HintSender,
    harry: dto.Player,
    dao: HolderDao,
    bot_session: BaseSession,
):
    await hint_sender.resolver.storage.put_content(FILE_META.local_file_name, BytesIO(b"12345"))
    await hint_sender.resolver.dao.upsert(file=FILE_META, author=harry)
    await hint_sender.resolver.dao.commit()
    session = typing.cast(MagicMock, bot_session)
    sent_message = Message(
        message_id=1,
        date=datetime.now(tz=timezone.utc),
        chat=Chat(id=CHAT_ID, type="private"),
        photo=[PhotoSize(file_id="RENEWED_FILE_ID", file_unique_id="u", width=1, height=1)],
    )
    session.side_effect = [
        TelegramAPIError(message="", method=SendPhoto),
        sent_message,
    ]

    await hint_sender.send_hint(PhotoHint(file_guid=GUID), CHAT_ID)

    renewed = await dao.file_info.get_by_guid(GUID)
    assert renewed.tg_link.file_id == "RENEWED_FILE_ID"
