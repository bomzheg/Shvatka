import typing
from unittest.mock import MagicMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.methods import SendMessage
from aiogram_dialog.test_tools import BotClient

from shvatka.core.models import dto
from shvatka.core.models import enums
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.views.commands import OTL_COMMAND
from tests.fixtures.chat_constants import create_tg_chat
from tests.fixtures.user_constants import create_tg_from_dto


@pytest.fixture
def harry_client(harry: dto.Player, dp: Dispatcher, bot: Bot):
    client = BotClient(dp, bot=bot)
    client.user = create_tg_from_dto(harry._user)
    client.chat = create_tg_chat(
        id_=client.user.id,
        type_=enums.ChatType.private,
        first_name=client.user.first_name,
        last_name=client.user.last_name,
    )
    return client


@pytest.mark.asyncio
async def test_otl_command(
    harry: dto.Player,
    harry_client: BotClient,
    dao: HolderDao,
    bot_session: BaseSession,
):
    await assert_otl_send_link(harry, harry_client, dao, bot_session)


@pytest.mark.asyncio
async def test_otl_command_on_started_game(
    started_game: dto.FullGame,
    harry: dto.Player,
    harry_client: BotClient,
    dao: HolderDao,
    bot_session: BaseSession,
):
    await assert_otl_send_link(harry, harry_client, dao, bot_session)


async def assert_otl_send_link(
    harry: dto.Player, client: BotClient, dao: HolderDao, bot_session: BaseSession
):
    session = typing.cast("MagicMock", bot_session)
    session.reset_mock(return_value=True, side_effect=True)

    await client.send("/" + OTL_COMMAND.command)

    sent = get_sent_methods(session, SendMessage)
    assert len(sent) == 1
    markup = sent[0].reply_markup
    assert markup is not None
    url = markup.inline_keyboard[0][0].url
    assert url is not None
    token = url.split("token=")[-1]
    assert await dao.one_time_token.get_invite(token) == {"player_id": harry.id}


def get_sent_methods(session: MagicMock, method_type: type) -> list:
    return [
        arg
        for call in session.await_args_list
        for arg in list(call.args) + list(call.kwargs.values())
        if isinstance(arg, method_type)
    ]
