from datetime import datetime

import pytest
from aiogram import Dispatcher, Bot
from aiogram.methods import SendMessage
from aiogram.types import Update, Message
from mockito import ANY

from app.dao.holder import HolderDao
from app.enums.chat_type import ChatType
from app.services.player import upsert_player, get_my_role
from app.services.user import upsert_user
from app.views.commands import CREATE_TEAM_COMMAND, ADD_IN_TEAM_COMMAND
from tests.fixtures.chat_constants import create_tg_chat
from tests.fixtures.user_constants import create_tg_user, create_dto_hermione, create_tg_from_dto
from tests.mocks.aiogram_mocks import mock_chat_owners, mock_get_chat, mock_reply, mock_chat_member


@pytest.mark.asyncio
async def test_create_team(dp: Dispatcher, bot: Bot, dao: HolderDao):
    chat = create_tg_chat(type_=ChatType.supergroup)
    harry = create_tg_user()
    mock_chat_owners(bot, chat.id, harry)
    mock_get_chat(bot, chat)
    mock_reply(bot, ANY(SendMessage))
    update = Update(
        update_id=1,
        message=Message(
            message_id=2,
            from_user=harry,
            chat=chat,
            text="/" + CREATE_TEAM_COMMAND.command,
            date=datetime.utcnow(),
        ),
    )
    await dp.feed_update(bot, update)
    assert await dao.team.count() == 1
    assert await dao.player_in_team.count() == 1
    team = (await dao.team._get_all())[0]

    assert chat.title == team.name

    hermi = create_dto_hermione()
    hermi_message = Message(
        message_id=3,
        from_user=create_tg_from_dto(hermi),
        chat=chat,
        text="hi everyone",
        date=datetime.utcnow(),
    )
    update = Update(
        update_id=2,
        message=hermi_message,
    )
    await dp.feed_update(bot, update)

    mock_chat_member(bot, chat.id, create_tg_from_dto(hermi))
    mock_reply(bot, ANY(SendMessage))
    update = Update(
        update_id=3,
        message=Message(
            message_id=4,
            from_user=harry,
            chat=chat,
            text=f"/{ADD_IN_TEAM_COMMAND.command} brain",
            reply_to_message=hermi_message,
            date=datetime.utcnow(),
        ),
    )
    await dp.feed_update(bot, update)
    assert await dao.player_in_team.count() == 2
    player = await upsert_player(await upsert_user(hermi, dao.user), dao.player)
    assert await get_my_role(player, dao.player_in_team) == "brain"
