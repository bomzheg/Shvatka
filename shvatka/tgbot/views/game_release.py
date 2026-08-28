import typing
import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import (
    InputMediaAnimation,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
)

from shvatka.core.models import dto, enums
from shvatka.core.models.dto import hints
from shvatka.core.views.game import GameReleasePublisher
from shvatka.infrastructure.db.dao import GameDao
from shvatka.tgbot.models.hint import BaseHintLinkView
from shvatka.tgbot.views.hint_factory.hint_content_resolver import HintContentResolver
from shvatka.tgbot.views.hint_sender import HintSender
from shvatka.tgbot.views.utils import total_remove_msg

logger = logging.getLogger(__name__)

EditableMedia: typing.TypeAlias = (
    InputMediaPhoto | InputMediaVideo | InputMediaAnimation | InputMediaAudio | InputMediaDocument
)

INPUT_MEDIA: dict[enums.HintType, type[EditableMedia]] = {
    enums.HintType.photo: InputMediaPhoto,
    enums.HintType.video: InputMediaVideo,
    enums.HintType.animation: InputMediaAnimation,
    enums.HintType.audio: InputMediaAudio,
    enums.HintType.document: InputMediaDocument,
}
"""Hint types telegram lets us swap into an already posted message."""


@dataclass
class GameBotReleasePublisher(GameReleasePublisher):
    """Keeps a game's release in the announcements channel, one message per part.

    A release is posted once and edited in place afterwards, so the channel
    keeps a single announcement per game instead of a pile of revisions. When
    the shape of the release changed too much for telegram to edit it (a hint
    added, removed or turned into another kind of content), the old messages
    are dropped and the release is posted anew.

    Which messages those are is the bot's own bookkeeping: it is stored beside
    the game but read and written only here, never through the domain — the
    same arrangement as an action request's bot messages.
    """

    bot: Bot
    hint_sender: HintSender
    resolver: HintContentResolver
    dao: GameDao
    log_chat_id: int

    async def publish(self, game: dto.Game, release: dto.GameRelease) -> None:
        posted = await self.dao.get_release_post(game.id)
        if posted:
            if await self.edit(release, posted):
                return
            await self.take_down(game.id, posted)
        await self.post(release)

    async def update(self, game: dto.Game, release: dto.GameRelease) -> None:
        """Only refresh what is already up — never announce a game by itself."""
        posted = await self.dao.get_release_post(game.id)
        if not posted:
            return
        if await self.edit(release, posted):
            return
        await self.take_down(game.id, posted)
        await self.post(release)

    async def post(self, release: dto.GameRelease) -> None:
        posted = []
        for hint in release.parts:
            message = await self.hint_sender.send_hint(hint, self.log_chat_id)
            posted.append(dto.BotMessage(chat_id=self.log_chat_id, message_id=message.message_id))
        await self.dao.save_release_post(release.game_id, posted)
        await self.dao.commit()
        logger.info("release of game %s posted to chat %s", release.game_id, self.log_chat_id)

    async def edit(self, release: dto.GameRelease, posted: list[dto.BotMessage]) -> bool:
        """Update the posted messages in place. False if telegram won't have it."""
        parts = release.parts
        if len(parts) != len(posted):
            return False
        for hint, message in zip(parts, posted, strict=False):
            if not await self.edit_one(hint, message):
                return False
        logger.info("release of game %s edited in chat %s", release.game_id, self.log_chat_id)
        return True

    async def edit_one(self, hint: hints.BaseHint, message: dto.BotMessage) -> bool:
        view = await self.resolver.resolve_link(hint)
        type_ = enums.HintType[hint.type]
        try:
            if type_ == enums.HintType.text:
                await self.bot.edit_message_text(
                    chat_id=message.chat_id, message_id=message.message_id, **view.kwargs()
                )
            else:
                media = self.to_input_media(type_, view)
                if media is None:
                    return False
                await self.bot.edit_message_media(
                    chat_id=message.chat_id, message_id=message.message_id, media=media
                )
        except TelegramBadRequest as e:
            if "not modified" in str(e):
                return True  # this part of the release did not change
            logger.info("can't edit release message %s in place", message, exc_info=e)
            return False
        except TelegramAPIError as e:
            logger.warning("can't edit release message %s", message, exc_info=e)
            return False
        return True

    @staticmethod
    def to_input_media(type_: enums.HintType, view: BaseHintLinkView) -> EditableMedia | None:
        """The posted message's new content, when it is a kind telegram can swap."""
        input_media = INPUT_MEDIA.get(type_)
        file_id = getattr(view, "file_id", None)
        if input_media is None or file_id is None:
            # locations, contacts, stickers, voices and video notes cannot be
            # swapped; neither can a file telegram has never seen
            return None
        kwargs = view.kwargs()
        media = input_media(media=file_id, caption=kwargs.get("caption"))
        if isinstance(media, InputMediaPhoto | InputMediaVideo | InputMediaAnimation):
            media.show_caption_above_media = kwargs.get("show_caption_above_media")
        return media

    async def unpublish(self, game: dto.Game) -> None:
        posted = await self.dao.get_release_post(game.id)
        if not posted:
            return
        await self.take_down(game.id, posted)

    async def take_down(self, game_id: int, posted: list[dto.BotMessage]) -> None:
        for message in posted:
            # a message too old to delete is struck through instead, so the
            # channel never keeps a release that no longer exists
            await total_remove_msg(self.bot, chat_id=message.chat_id, msg_id=message.message_id)
        await self.dao.clear_release_post(game_id)
        await self.dao.commit()
