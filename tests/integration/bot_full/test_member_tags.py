import dataclasses
import typing
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from dishka import AsyncContainer

from shvatka.core.models import dto
from shvatka.core.players.player import get_full_team_player, join_team, leave
from shvatka.core.services.team import rename_team
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.services.bot_rights import BotRights, ChatRights
from shvatka.tgbot.services.member_tags import MemberTagger, render_tag
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
async def notifier(dishka: AsyncContainer, bot: Bot, dao: HolderDao):
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
        team_players_dao=dao.team_player,
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
    assert tag.chat_id == PUBLIC_CHAT
    assert hermione.get_chat_id() == tag.user_id
    # the team name is longer than the 16 characters telegram allows in a tag
    assert render_tag(gryffindor.name) == tag.tag

    await leave(hermione, hermione, dao.team_leaver, notifier=notifier)

    _, cleared = tags(bot_session)
    assert hermione.get_chat_id() == cleared.user_id
    assert cleared.tag is None


@pytest.mark.asyncio
async def test_tags_follow_team_rename(
    harry: dto.Player,
    hermione: dto.Player,
    gryffindor: dto.Team,
    dao: HolderDao,
    notifier: BotTeamNotifier,
    bot_session: BaseSession,
):
    await join_team(hermione, gryffindor, harry, dao.team_player, notifier=notifier)
    captain = await get_full_team_player(harry, gryffindor, dao.team_player)

    await rename_team(gryffindor, captain, "Гриффиндор", dao.team, notifier)

    _, *retagged = tags(bot_session)
    assert {harry.get_chat_id(), hermione.get_chat_id()} == {tag.user_id for tag in retagged}
    assert {render_tag("Гриффиндор")} == {tag.tag for tag in retagged}
