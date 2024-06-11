from datetime import datetime

import pytest
from aiogram import Dispatcher
from aiogram.enums import ChatMemberStatus
from aiogram.methods import SendMessage, GetChatAdministrators, GetChat, GetChatMember
from aiogram.types import Update, Message, ChatMemberOwner, ChatMemberMember
from aiogram_tests.mocked_bot import MockedBot

from shvatka.core.models import dto
from shvatka.core.models.enums.chat_type import ChatType
from shvatka.core.services.player import upsert_player, get_my_role
from shvatka.core.services.user import upsert_user
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.views.commands import CREATE_TEAM_COMMAND, ADD_IN_TEAM_COMMAND
from tests.fixtures.chat_constants import create_tg_chat
from tests.fixtures.player import promote
from tests.fixtures.user_constants import (
    create_tg_user,
    create_dto_hermione,
    create_tg_from_dto,
)


@pytest.mark.skip(reason="doesnt work. TODO")
@pytest.mark.asyncio
async def test_create_team(harry: dto.Player, dp: Dispatcher, bot: MockedBot, dao: HolderDao):
    await promote(harry, dao)
    chat = create_tg_chat(type_=ChatType.supergroup)
    harry_tg = create_tg_user()
    bot.add_result_for(
        GetChatAdministrators,
        ok=True,
        result=[
            ChatMemberOwner(user=harry_tg, is_anonymous=False, status=ChatMemberStatus.CREATOR)
        ],
    )
    bot.add_result_for(GetChat, ok=True, result=chat)
    bot.add_result_for(SendMessage, ok=True)  # one for captain
    bot.add_result_for(SendMessage, ok=True)  # one for log
    update = Update(
        update_id=1,
        message=Message(
            message_id=2,
            from_user=harry_tg,
            chat=chat,
            text="/" + CREATE_TEAM_COMMAND.command,
            date=datetime.now(tz=tz_utc),
        ),
    )
    await dp.feed_update(bot, update)
    assert await dao.team.count() == 1
    assert await dao.team_player.count() == 1
    team = (await dao.team._get_all())[0]

    assert chat.title == team.name

    hermi = create_dto_hermione()
    hermi_message = Message(
        message_id=3,
        from_user=create_tg_from_dto(hermi),
        chat=chat,
        text="hi everyone",
        date=datetime.now(tz=tz_utc),
    )
    update = Update(
        update_id=2,
        message=hermi_message,
    )
    await dp.feed_update(bot, update)

    bot.session.responses.clear()
    bot.session.requests.clear()
    bot.add_result_for(
        method=GetChatMember,
        ok=True,
        result=ChatMemberMember(user=create_tg_from_dto(hermi), status=ChatMemberStatus.MEMBER),
    )
    bot.add_result_for(SendMessage, ok=True)
    update = Update(
        update_id=3,
        message=Message(
            message_id=4,
            from_user=harry_tg,
            chat=chat,
            text=f"/{ADD_IN_TEAM_COMMAND.command} brain",
            reply_to_message=hermi_message,
            date=datetime.now(tz=tz_utc),
        ),
    )
    await dp.feed_update(bot, update)
    assert await dao.team_player.count() == 2
    player = await upsert_player(await upsert_user(hermi, dao.user), dao.player)
    assert await get_my_role(player, dao.team_player) == "brain"
