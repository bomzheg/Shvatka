import pytest
from aiogram import Dispatcher, Bot
from aiogram_dialog.test_tools import BotClient

from shvatka.models import dto, enums
from tests.fixtures.chat_constants import create_tg_chat
from tests.fixtures.user_constants import create_tg_from_dto


@pytest.fixture
def author_client(author: dto.Player, dp: Dispatcher, bot: Bot):
    client = BotClient(dp, bot=bot)
    client.user = create_tg_from_dto(author.user)
    client.chat = create_tg_chat(
        type_=enums.ChatType.private,
        first_name=client.user.first_name,
        last_name=client.user.last_name,
    )
    return client
