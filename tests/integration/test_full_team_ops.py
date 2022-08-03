from datetime import datetime

import pytest
from aiogram import Dispatcher, Bot
from aiogram.methods import SendMessage
from aiogram.types import Update, Message
from mockito import ANY

from app.dao.holder import HolderDao
from app.enums.chat_type import ChatType
from app.views.commands import CREATE_TEAM_COMMAND
from tests.fixtures.chat_constants import create_tg_chat
from tests.fixtures.user_constants import create_tg_user
from tests.mocks.aiogram_mocks import mock_chat_owners, mock_get_chat, mock_reply


@pytest.mark.asyncio
async def test_create_team(dp: Dispatcher, bot: Bot, dao: HolderDao):
    chat = create_tg_chat(type_=ChatType.supergroup)
    user = create_tg_user()
    mock_chat_owners(bot, chat.id, user)
    mock_get_chat(bot, chat)
    mock_reply(bot, ANY(SendMessage))
    update = Update(
        update_id=1,
        message=Message(
            message_id=2,
            from_user=user,
            chat=chat,
            text="/" + CREATE_TEAM_COMMAND.command,
            date=datetime.utcnow(),
        ),
    )
    await dp.feed_update(bot, update)
    assert await dao.team.count() == 1
    team = (await dao.team.get_all())[0]

    assert chat.title == team.name
