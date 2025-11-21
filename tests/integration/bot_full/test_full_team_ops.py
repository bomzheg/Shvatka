import typing
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from aiogram import Dispatcher, Bot
from aiogram.client.session.base import BaseSession
from aiogram.enums import ChatMemberStatus
from aiogram.types import Update, Message, ChatMemberOwner, ChatMemberMember

from shvatka.core.models import dto
from shvatka.core.models.enums.chat_type import ChatType
from shvatka.core.services.player import upsert_player, get_my_role
from shvatka.core.services.user import upsert_user
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.views.commands import CREATE_TEAM_COMMAND, ADD_IN_TEAM_COMMAND
from tests.fixtures.chat_constants import create_tg_chat, chat_to_full_chat
from tests.fixtures.player import promote
from tests.fixtures.user_constants import (
    create_tg_user,
    create_dto_hermione,
    create_tg_from_dto,
)


@pytest.mark.asyncio
async def test_create_team(
    harry: dto.Player, dp: Dispatcher, bot: Bot, dao: HolderDao, bot_session: BaseSession
):
    await promote(harry, dao)
    chat = create_tg_chat(type_=ChatType.supergroup)
    harry_tg = create_tg_user()
    session = typing.cast(MagicMock, bot_session)
    session.side_effect = [
        [ChatMemberOwner(user=harry_tg, is_anonymous=False, status=ChatMemberStatus.CREATOR)],
        chat_to_full_chat(chat),
        {},
        {},
    ]
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

    session.reset_mock(return_value=True, side_effect=True)
    session.side_effect = [
        ChatMemberMember(user=create_tg_from_dto(hermi), status=ChatMemberStatus.MEMBER),
        {},
    ]
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
