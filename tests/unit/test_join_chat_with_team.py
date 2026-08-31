"""The join offer is about the newcomer, not about whoever let them in.

A chat_member update carries the member who caused the change as its user, so
resolving the player from the identity names the inviting captain instead of
the person who joined — and the accept button then carries the captain's id.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.types import Chat, ChatMemberLeft, ChatMemberMember, ChatMemberUpdated, User
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.aiogram import CONTAINER_NAME

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums.chat_type import ChatType
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.handlers.team.manage import user_join_chat_with_team
from shvatka.tgbot.keyboards.team import JoinToTeamRequestCD

TEAM_CHAT_ID = -1001
CAPTAIN = User(id=1, is_bot=False, first_name="Юрий", username="bomzheg")
NEWCOMER = User(id=2, is_bot=False, first_name="Оператор", username="opr")
A_BOT = User(id=3, is_bot=True, first_name="SomeBot", username="some_bot")

CAPTAIN_PLAYER = dto.Player(id=10, can_be_author=True, is_dummy=False, username="bomzheg")
NEWCOMER_PLAYER = dto.Player(id=20, can_be_author=False, is_dummy=False, username="opr")


def team() -> dto.Team:
    return dto.TeamWithCaptain(
        id=5,
        name="like a team",
        captain=CAPTAIN_PLAYER,
        is_dummy=False,
        description=None,
        chat=dto.Chat(tg_id=TEAM_CHAT_ID, type=ChatType.supergroup, title="team chat"),
    )


def joined_event(who: User) -> ChatMemberUpdated:
    return ChatMemberUpdated(
        chat=Chat(id=TEAM_CHAT_ID, type="supergroup"),
        from_user=CAPTAIN,
        date=datetime.now(tz=UTC),
        old_chat_member=ChatMemberLeft(status="left", user=who),
        new_chat_member=ChatMemberMember(status="member", user=who),
    )


async def call(event: ChatMemberUpdated) -> AsyncMock:
    bot = AsyncMock(Bot)
    dao = AsyncMock()
    dao.user.upsert_user.return_value = dto.User(tg_id=NEWCOMER.id, first_name="Оператор")
    dao.player.upsert_player.return_value = NEWCOMER_PLAYER
    identity = AsyncMock(IdentityProvider)
    identity.get_required_team.return_value = team()
    identity.get_required_player.return_value = CAPTAIN_PLAYER

    class IdpProvider(Provider):
        scope = Scope.REQUEST

        @provide
        def idp(self) -> IdentityProvider:
            return identity

        @provide
        def holder(self) -> HolderDao:
            return dao

    container = make_async_container(IdpProvider())
    try:
        async with container() as request_container:
            await user_join_chat_with_team(event, bot=bot, **{CONTAINER_NAME: request_container})
    finally:
        await container.close()
    return bot


@pytest.mark.asyncio
async def test_offer_names_the_newcomer_not_the_inviter():
    bot = await call(joined_event(NEWCOMER))

    bot.send_message.assert_awaited_once()
    text = bot.send_message.await_args.kwargs["text"]
    assert "opr" in text
    assert "bomzheg" not in text


@pytest.mark.asyncio
async def test_accept_button_carries_the_newcomer():
    bot = await call(joined_event(NEWCOMER))

    markup = bot.send_message.await_args.kwargs["reply_markup"]
    buttons = [button for row in markup.inline_keyboard for button in row]
    for button in buttons:
        assert JoinToTeamRequestCD.unpack(button.callback_data).player_id == NEWCOMER_PLAYER.id


@pytest.mark.asyncio
async def test_a_joining_bot_is_ignored():
    bot = await call(joined_event(A_BOT))
    bot.send_message.assert_not_awaited()
