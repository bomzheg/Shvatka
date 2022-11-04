import typing
from unittest.mock import Mock

import pytest
import pytest_asyncio
from aiogram import Bot

from db.dao.holder import HolderDao
from shvatka.clients.file_storage import FileStorage
from shvatka.models import dto
from shvatka.models.dto.scn import TextHint, GPSHint, PhotoHint, FileContent, FileContentLink, TgLink
from shvatka.models.dto.scn.hint_part import VenueHint
from shvatka.models.enums.hint_type import HintType
from tests.fixtures.scn_fixtures import GUID
from tests.mocks.aiogram_mocks import mock_coro
from tgbot.views.hint_content_resolver import HintContentResolver
from tgbot.views.hint_sender import HintSender

FILE_ID = "98765"
CHAT_ID = 111
FILE_CONTENT = FileContent(
    guid=GUID,
    tg_link=TgLink(file_id=FILE_ID, content_type=HintType.photo),
    extension=".jpg",
    file_content_link=FileContentLink(file_path=""),
    original_filename="файло",
)

@pytest_asyncio.fixture
async def hint_sender(bot: Bot, dao: HolderDao, file_storage: FileStorage):
    bot = typing.cast(Mock, bot)
    bot.reset_mock()
    bot.send_message = Mock(return_value=mock_coro(None))
    bot.send_location = Mock(return_value=mock_coro(None))
    bot.send_venue = Mock(return_value=mock_coro(None))
    bot.send_photo = Mock(return_value=mock_coro(None))
    bot.send_audio = Mock(return_value=mock_coro(None))
    bot.send_video = Mock(return_value=mock_coro(None))
    bot.send_document = Mock(return_value=mock_coro(None))
    bot.send_animation = Mock(return_value=mock_coro(None))
    bot.send_voice = Mock(return_value=mock_coro(None))
    bot.send_video_note = Mock(return_value=mock_coro(None))
    bot.send_contact = Mock(return_value=mock_coro(None))
    bot.send_sticker = Mock(return_value=mock_coro(None))

    return HintSender(bot=bot, resolver=HintContentResolver(dao=dao.file_info, file_storage=file_storage))


@pytest.mark.asyncio
async def test_send_text(hint_sender: HintSender):
    hint = TextHint(text="Привет")
    await hint_sender.send_hint(hint, CHAT_ID)
    mock: Mock = typing.cast(Mock, hint_sender.bot)
    mock.send_message.assert_called_once_with(chat_id=CHAT_ID, text=hint.text)


@pytest.mark.asyncio
async def test_send_location(hint_sender: HintSender):
    hint = GPSHint(longitude=55.59, latitude=37.88)
    await hint_sender.send_hint(hint, CHAT_ID)
    mock: Mock = typing.cast(Mock, hint_sender.bot)
    mock.send_location.assert_called_once_with(chat_id=CHAT_ID, longitude=hint.longitude, latitude=hint.latitude)


@pytest.mark.asyncio
async def test_send_venue(hint_sender: HintSender):
    hint = VenueHint(longitude=55.59, latitude=37.88, title="awesome cafe", address="Ленина, 1")
    await hint_sender.send_hint(hint, CHAT_ID)
    mock: Mock = typing.cast(Mock, hint_sender.bot)
    mock.send_venue.assert_called_once_with(
        chat_id=CHAT_ID,
        longitude=hint.longitude,
        latitude=hint.latitude,
        title=hint.title,
        address=hint.address,
        foursquare_id=hint.foursquare_id,
        foursquare_type=hint.foursquare_type,
    )

@pytest.mark.asyncio
async def test_send_photo_by_id(hint_sender: HintSender, harry: dto.Player):
    await hint_sender.resolver.dao.upsert(file=FILE_CONTENT, author=harry)
    await hint_sender.resolver.dao.commit()
    hint = PhotoHint(file_guid=GUID)
    await hint_sender.send_hint(hint, CHAT_ID)
    mock: Mock = typing.cast(Mock, hint_sender.bot)
    mock.send_photo.assert_called_once_with(chat_id=CHAT_ID, photo=FILE_ID, caption=None)

