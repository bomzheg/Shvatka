import typing
from io import BytesIO
from typing import Type

import pytest
import pytest_asyncio
from aiogram.methods import (
    SendMessage,
    SendLocation,
    SendPhoto,
    SendVenue,
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
from aiogram_tests.mocked_bot import MockedBot

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models import dto
from shvatka.core.models.dto.scn import TextHint, GPSHint, PhotoHint, BaseHint
from shvatka.core.models.dto.scn.hint_part import (
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
from shvatka.tgbot.views.hint_factory.hint_content_resolver import HintContentResolver
from shvatka.tgbot.views.hint_sender import HintSender
from tests.fixtures.file_storage_constants import FILE_ID, CHAT_ID, FILE_META
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
async def hint_sender(dao: HolderDao, file_storage: FileStorage):
    bot = MockedBot()
    return HintSender(
        bot=bot, resolver=HintContentResolver(dao=dao.file_info, file_storage=file_storage)
    )


@pytest.mark.asyncio
async def test_send_text(hint_sender: HintSender):
    hint = TextHint(text="Привет")

    bot = typing.cast(MockedBot, hint_sender.bot)
    bot.add_result_for(method=SendMessage, ok=True)
    await hint_sender.send_hint(hint, CHAT_ID)

    request = bot.session.requests.pop()
    assert request.method == "sendMessage"
    assert request.data["text"] == hint.text
    assert 0 == len(bot.session.requests)


@pytest.mark.asyncio
async def test_send_location(hint_sender: HintSender):
    hint = GPSHint(longitude=55.59, latitude=37.88)

    bot = typing.cast(MockedBot, hint_sender.bot)
    bot.add_result_for(method=SendLocation, ok=True)
    await hint_sender.send_hint(hint, CHAT_ID)

    request = bot.session.requests.pop()
    assert request.method == "sendLocation"
    assert request.data["longitude"] == hint.longitude
    assert request.data["latitude"] == hint.latitude
    assert 0 == len(bot.session.requests)


@pytest.mark.asyncio
async def test_send_venue(hint_sender: HintSender):
    hint = VenueHint(longitude=55.59, latitude=37.88, title="awesome cafe", address="Ленина, 1")
    bot = typing.cast(MockedBot, hint_sender.bot)

    bot.add_result_for(method=SendVenue, ok=True)
    await hint_sender.send_hint(hint, CHAT_ID)

    request = bot.session.requests.pop()
    assert request.method == "sendVenue"
    assert request.data["longitude"] == hint.longitude
    assert request.data["latitude"] == hint.latitude
    assert request.data["title"] == hint.title
    assert request.data["address"] == hint.address
    assert request.data["foursquare_id"] == hint.foursquare_id
    assert request.data["foursquare_type"] == hint.foursquare_type
    assert 0 == len(bot.session.requests)


@pytest.mark.asyncio
@pytest.mark.parametrize("tg_method,hint,method_name,content_type", PARAMETERS)
async def test_send_photo_by_id(
    hint_sender: HintSender,
    harry: dto.Player,
    hint: BaseHint,
    tg_method: Type[TelegramMethod[TelegramType]],
    method_name: str,
    content_type: str,
):
    await hint_sender.resolver.dao.upsert(file=FILE_META, author=harry)
    await hint_sender.resolver.dao.commit()

    bot = typing.cast(MockedBot, hint_sender.bot)
    bot.add_result_for(method=tg_method, ok=True)
    await hint_sender.send_hint(hint, CHAT_ID)

    request = bot.session.requests.pop()
    assert request.method == method_name
    assert request.data[content_type] == FILE_ID
    assert 0 == len(bot.session.requests)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tg_method,hint,method_name,content_type", PARAMETERS[:-1]
)  # we don't send sticker by content
async def test_send_photo_by_content(
    hint_sender: HintSender,
    harry: dto.Player,
    hint: BaseHint,
    tg_method: Type[TelegramMethod[TelegramType]],
    method_name: str,
    content_type: str,
):
    await hint_sender.resolver.storage.put_content(FILE_META.local_file_name, BytesIO(b"12345"))
    await hint_sender.resolver.dao.upsert(file=FILE_META, author=harry)
    await hint_sender.resolver.dao.commit()

    bot = typing.cast(MockedBot, hint_sender.bot)
    bot.add_result_for(method=tg_method, ok=False, error_code=400, description=BAD_REQUEST_DESC)
    bot.add_result_for(method=tg_method, ok=True)

    await hint_sender.send_hint(hint, CHAT_ID)

    assert 2 == len(bot.session.requests)
    request = bot.session.requests.popleft()
    assert request.method == method_name
    assert request.data[content_type] == FILE_ID

    request = bot.session.requests.popleft()
    assert request.method == method_name
    assert request.files[content_type] is not None
    assert 0 == len(bot.session.requests)
