import logging

from aiogram import F, Router
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.services.member_tags import MemberTagger

logger = logging.getLogger(__name__)


@inject
async def user_joined_public_chat(
    event: ChatMemberUpdated,
    tagger: FromDishka[MemberTagger],
    dao: FromDishka[HolderDao],
) -> None:
    """
    A tag lives in the chat, not in the database, so a player who joins the
    chat later than their team has no tag until they get one here.
    """
    user = event.new_chat_member.user
    if user.is_bot:
        return
    try:
        player = await dao.player.get_by_user(await dao.user.get_by_tg_id(user.id))
    except (exceptions.UserNotFoundError, exceptions.PlayerNotFoundError):
        return
    if (team := await dao.team_player.get_team(player)) is None:
        return
    await tagger.sync_in_chat(event.chat.id, player, team)


def setup(config: BotConfig) -> Router:
    router = Router(name=__name__)
    router.chat_member.register(
        user_joined_public_chat,
        ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER),
        F.chat.id.in_(config.public_chats),
    )
    return router
