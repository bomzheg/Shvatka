import logging
import typing
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
from shvatka.tgbot.models.hint import BaseHintLinkView
from shvatka.tgbot.views.hint_factory.hint_content_resolver import HintContentResolver
from shvatka.tgbot.views.hint_sender import HintSender

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
    """

    bot: Bot
    hint_sender: HintSender
    resolver: HintContentResolver
    log_chat_id: int

    async def publish(self, game: dto.Game, release: dto.GameRelease) -> dto.ReleasePost | None:
        posted = release.post
        if posted is not None:
            if await self.edit(release, posted):
                return posted
            await self.unpublish(game, posted)
        return await self.post(release)

    async def post(self, release: dto.GameRelease) -> dto.ReleasePost:
        message_ids = []
        for hint in release.parts:
            message = await self.hint_sender.send_hint(hint, self.log_chat_id)
            message_ids.append(message.message_id)
        logger.info("release of game %s posted to chat %s", release.game_id, self.log_chat_id)
        return dto.ReleasePost(chat_id=self.log_chat_id, message_ids=message_ids)

    async def edit(self, release: dto.GameRelease, post: dto.ReleasePost) -> bool:
        """Update the posted messages in place. False if telegram won't have it."""
        parts = release.parts
        if len(parts) != len(post.message_ids):
            return False
        for hint, message_id in zip(parts, post.message_ids):
            if not await self.edit_one(hint, post.chat_id, message_id):
                return False
        logger.info("release of game %s edited in chat %s", release.game_id, post.chat_id)
        return True

    async def edit_one(self, hint: hints.BaseHint, chat_id: int, message_id: int) -> bool:
        view = await self.resolver.resolve_link(hint)
        type_ = enums.HintType[hint.type]
        try:
            if type_ == enums.HintType.text:
                await self.bot.edit_message_text(
                    chat_id=chat_id, message_id=message_id, **view.kwargs()
                )
            else:
                media = self.to_input_media(type_, view)
                if media is None:
                    return False
                await self.bot.edit_message_media(
                    chat_id=chat_id, message_id=message_id, media=media
                )
        except TelegramBadRequest as e:
            if "not modified" in str(e):
                return True  # this part of the release did not change
            logger.info("can't edit release message %s in place", message_id, exc_info=e)
            return False
        except TelegramAPIError as e:
            logger.warning("can't edit release message %s", message_id, exc_info=e)
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

    async def unpublish(self, game: dto.Game, post: dto.ReleasePost) -> None:
        for message_id in post.message_ids:
            await self.delete_one(post.chat_id, message_id)

    async def delete_one(self, chat_id: int, message_id: int) -> None:
        try:
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except TelegramAPIError as e:
            # an already deleted (or too old) message must not block the rest
            logger.info("can't delete release message %s", message_id, exc_info=e)
