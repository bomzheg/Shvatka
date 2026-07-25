import logging
import unicodedata
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from shvatka.core.models import dto
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.services.bot_rights import BotRights

logger = logging.getLogger(__name__)

TAG_MAX_LENGTH = 16
"""telegram allows 0-16 characters in a member tag"""

JOINERS = frozenset(
    (
        "\u200d",  # zero width joiner
        "\ufe0e",  # variation selector-15 (text presentation)
        "\ufe0f",  # variation selector-16 (emoji presentation)
        "\u20e3",  # combining enclosing keycap
    )
)
SKIN_TONES = ("\U0001f3fb", "\U0001f3ff")


def is_emoji(char: str) -> bool:
    """Telegram forbids emoji in member tags, so they have to be cut out."""
    if char in JOINERS:
        return True
    if SKIN_TONES[0] <= char <= SKIN_TONES[1]:
        return True
    return unicodedata.category(char) == "So"


def render_tag(name: str) -> str | None:
    """Team name as a member tag: no emoji, no more than 16 characters."""
    cleaned = " ".join("".join(c for c in name if not is_emoji(c)).split())
    return cleaned[:TAG_MAX_LENGTH].strip() or None


@dataclass
class MemberTagger:
    """
    Marks players in public chats with the name of their team.

    Tagging requires the can_manage_tags right, which the bot may not have
    (and in some chats it is not even an admin), so every failure is only
    logged: a missing tag must not break the action that caused it.
    """

    bot: Bot
    config: BotConfig
    bot_rights: BotRights

    async def sync(self, player: dto.Player, team: dto.Team | None) -> None:
        """Set (or clear, if there is no team) the tag in every public chat."""
        for chat_id in self.config.public_chats:
            await self.sync_in_chat(chat_id, player, team)

    async def sync_in_chat(self, chat_id: int, player: dto.Player, team: dto.Team | None) -> None:
        user_id = player.get_chat_id()
        if user_id is None:
            # dummy, forum-only or email-only player, there is nobody to tag
            return
        if not await self.bot_rights.can_manage_tags(chat_id):
            logger.debug("can't manage tags in chat %s, skip player %s", chat_id, player.id)
            return
        tag = render_tag(team.name) if team is not None else None
        try:
            await self.bot.set_chat_member_tag(chat_id=chat_id, user_id=user_id, tag=tag)
        except TelegramAPIError as e:
            # the player may be not a member of that chat at all - it's expected
            logger.info(
                "can't set tag %s for player %s in chat %s", tag, player.id, chat_id, exc_info=e
            )
        else:
            logger.info("tag of player %s in chat %s set to %s", player.id, chat_id, tag)
