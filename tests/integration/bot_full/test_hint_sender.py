import typing
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramAPIError
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
from aiogram.types import Chat, Message, PhotoSize
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models import dto
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
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.config.models.main import TgBotConfig
from shvatka.tgbot.views.hint_factory.hint_content_resolver import HintContentResolver
from shvatka.tgbot.views.hint_sender import HintSender
from tests.fixtures.file_storage import FILE_ID, CHAT_ID, FILE_META, NO_FILE_ID_META
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
    dishka_request: AsyncContainer,
):
    bot = Bot(token=bot_config.bot.token, session=bot_session)
    session_pool = await dishka_request.get(async_sessionmaker[AsyncSession])
    return HintSender(
        bot=bot,
        resolver=HintContentResolver(dao=dao.file_info, file_storage=file_storage),
        session_pool=session_pool,
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
async def test_send_by_content_when_file_id_is_missing(
    hint_sender: HintSender,
    harry: dto.Player,
    hint: BaseHint,
    tg_method: TelegramMethod[TelegramType],
    method_name: str,
    content_type: str,
    bot_session: BaseSession,
):
    await hint_sender.resolver.storage.put_content(
        NO_FILE_ID_META.local_file_name, BytesIO(b"12345")
    )
    await hint_sender.resolver.dao.upsert(file=NO_FILE_ID_META, author=harry)
    await hint_sender.resolver.dao.commit()
    session = typing.cast(MagicMock, bot_session)
    session.side_effect = [{}]

    await hint_sender.send_hint(hint, CHAT_ID)

    # no file_id -> we go straight to content, no failed attempt by file_id first
    assert 1 == session.call_count
    call = session.mock_calls.pop()
    request = call.args[1]
    assert request.__api_method__ == method_name
    assert getattr(request, content_type) is not None


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
async def test_send_by_content_saves_new_file_id(
    hint_sender: HintSender,
    harry: dto.Player,
    bot_session: BaseSession,
):
    new_file_id = "brand-new-file-id"
    hint = PhotoHint(file_guid=GUID)
    await hint_sender.resolver.storage.put_content(FILE_META.local_file_name, BytesIO(b"12345"))
    await hint_sender.resolver.dao.upsert(file=FILE_META, author=harry)
    await hint_sender.resolver.dao.commit()
    session = typing.cast(MagicMock, bot_session)
    session.side_effect = [
        TelegramAPIError(message="", method=SendPhoto),
        Message(
            message_id=1,
            date=datetime.now(timezone.utc),
            chat=Chat(id=CHAT_ID, type="private"),
            photo=[PhotoSize(file_id=new_file_id, file_unique_id="unique", width=10, height=10)],
        ),
    ]

    await hint_sender.send_hint(hint, CHAT_ID)

    saved = await hint_sender.resolver.dao.get_by_guid(GUID)
    assert saved.tg_link.file_id == new_file_id
