"""A dialog opened before the player left the team must not crash on a click.

Between opening a window and pressing a button in it any amount of time may
pass - the captain can remove the player meanwhile. See issue #339.
"""

import typing
from unittest.mock import MagicMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.methods import AnswerCallbackQuery
from aiogram.types import Message
from aiogram_dialog.test_tools import BotClient, MockMessageManager
from aiogram_dialog.test_tools.keyboard import InlineButtonTextLocator

from shvatka.core.models import dto, enums
from shvatka.core.players.player import (
    flip_permission,
    get_full_team_player,
    join_team,
    leave,
)
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.dialogs.outdated import NOT_IN_TEAM
from shvatka.tgbot.views.commands import START_COMMAND
from tests.fixtures.chat_constants import create_tg_chat
from tests.fixtures.user_constants import create_tg_from_dto
from tests.mocks.team_notifier import TeamNotifierMock

MY_TEAM_BUTTON = "🚩Моя команда"
MANAGE_TEAM_BUTTON = "🚩Управление командой"
PLAYERS_BUTTON = "👥Игроки"
# always in the main menu, whether the player has a team or not
TEAMS_BUTTON = "👥Команды"


@pytest.fixture
def hermione_client(hermione: dto.Player, dp: Dispatcher, bot: Bot) -> BotClient:
    client = BotClient(dp, bot=bot)
    client.user = create_tg_from_dto(hermione._user)
    client.chat = create_tg_chat(
        id_=client.user.id,
        type_=enums.ChatType.private,
        first_name=client.user.first_name,
        last_name=client.user.last_name,
    )
    return client


@pytest.mark.asyncio
async def test_my_team_opened_after_removed_from_team(
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    hermione_client: BotClient,
    message_manager: MockMessageManager,
    bot_session: BaseSession,
    dao: HolderDao,
):
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())
    main_menu = await open_main_menu(hermione_client, message_manager)

    await leave(player=hermione, remover=harry, dao=dao.team_leaver, notifier=TeamNotifierMock())

    message_manager.reset_history()
    await hermione_client.click(main_menu, InlineButtonTextLocator(MY_TEAM_BUTTON))

    assert_answered_with(bot_session, NOT_IN_TEAM)
    assert_main_menu_without(message_manager.last_message(), MY_TEAM_BUTTON)


@pytest.mark.asyncio
async def test_captains_bridge_opened_after_removed_from_team(
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    hermione_client: BotClient,
    message_manager: MockMessageManager,
    bot_session: BaseSession,
    dao: HolderDao,
):
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=TeamNotifierMock())
    await flip_permission(
        actor=await get_full_team_player(harry, gryffindor, dao.team_player),
        team_player=await get_full_team_player(hermione, gryffindor, dao.team_player),
        permission=enums.TeamPlayerPermission.can_manage_players,
        dao=dao.team_player,
    )
    main_menu = await open_main_menu(hermione_client, message_manager)

    message_manager.reset_history()
    await hermione_client.click(main_menu, InlineButtonTextLocator(MANAGE_TEAM_BUTTON))
    captains_bridge = message_manager.last_message()

    await leave(player=hermione, remover=harry, dao=dao.team_leaver, notifier=TeamNotifierMock())

    message_manager.reset_history()
    await hermione_client.click(captains_bridge, InlineButtonTextLocator(PLAYERS_BUTTON))

    assert_answered_with(bot_session, NOT_IN_TEAM)
    assert_main_menu_without(message_manager.last_message(), PLAYERS_BUTTON)


async def open_main_menu(client: BotClient, message_manager: MockMessageManager):
    message_manager.reset_history()
    await client.send("/" + START_COMMAND.command)
    return message_manager.last_message()


def assert_main_menu_without(message: Message, gone: str) -> None:
    """The user is dropped into a menu built from current data."""
    assert InlineButtonTextLocator(TEAMS_BUTTON).find_button(message) is not None
    assert InlineButtonTextLocator(gone).find_button(message) is None


def assert_answered_with(bot_session: BaseSession, text: str) -> None:
    session = typing.cast(MagicMock, bot_session)
    answers = [
        arg
        for call in session.await_args_list
        for arg in list(call.args) + list(call.kwargs.values())
        if isinstance(arg, AnswerCallbackQuery)
    ]
    assert [answer.text for answer in answers] == [text]
    assert answers[0].show_alert
