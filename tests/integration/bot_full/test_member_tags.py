import dataclasses
import typing
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from dishka import AsyncContainer

from shvatka.core.models import dto
from shvatka.core.players.player import join_team, leave
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.services.bot_rights import BotRights, ChatRights
from shvatka.tgbot.services.member_tags import MemberTagger
from shvatka.tgbot.views.team import BotTeamNotifier

PUBLIC_CHAT = -1001232232152
CAN_TAG = ChatRights(can_pin_messages=False, can_manage_tags=True)


def tags(bot_session: BaseSession) -> list:
    session = typing.cast(MagicMock, bot_session)
    return [
        call.args[1]
        for call in session.mock_calls
        if getattr(call.args[1], "__api_method__", None) == "setChatMemberTag"
    ]


@pytest_asyncio.fixture
async def notifier(dishka: AsyncContainer, bot: Bot):
    config = await dishka.get(BotConfig)
    rights = await dishka.get(BotRights)
    # rights are cached, so the tagger doesn't ask telegram about them
    rights.save(PUBLIC_CHAT, CAN_TAG)
    return BotTeamNotifier(
        bot=bot,
        tagger=MemberTagger(
            bot=bot,
            # the shared test config has no public chats, they'd affect other tests
            config=dataclasses.replace(config, public_chats=[PUBLIC_CHAT]),
            bot_rights=rights,
        ),
    )


@pytest.mark.asyncio
async def test_tag_set_and_cleared_on_team_ops(
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    dao: HolderDao,
    notifier: BotTeamNotifier,
    bot_session: BaseSession,
):
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=notifier)

    (tag,) = tags(bot_session)
    assert PUBLIC_CHAT == tag.chat_id
    assert hermione.get_chat_id() == tag.user_id
    assert gryffindor.name == tag.tag

    await leave(hermione, harry, dao.team_player, notifier=notifier)

    _, cleared = tags(bot_session)
    assert hermione.get_chat_id() == cleared.user_id
    assert cleared.tag is None
