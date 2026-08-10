"""Background tasks of the bot: work spawned through the app :class:`Nursery`.

Each task is a pair — a frozen params dataclass carrying the data of a single
run, and a class whose dependencies come from DI. The task runs in a scope of
its own, so the session-bound things it works with (a :class:`HintSender` and
its dao, for one) are acquired and finalized by that scope rather than borrowed
from the handler's, which is gone by the time the task starts.

Entities travel in params: they are plain dataclasses, detached from any
session, so handing a loaded game or level to a task is free. What must never
cross is a resource tied to the caller's scope — a dao, a session, a sender —
those come from DI inside the task.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.methods import TelegramMethod
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import BaseDialogManager
from dishka import Provider, Scope, from_context, provide
from telegraph.aio import Telegraph

from shvatka.core.models import dto
from shvatka.infrastructure.crawler.game_scn.uploader.forum_scenario_uploader import upload
from shvatka.infrastructure.crawler.game_scn.uploader.game_mapper import map_game_for_upload
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.views.hint_sender import HintSender
from shvatka.tgbot.views.results.scenario import GamePublisher, LevelPublisher

logger = logging.getLogger(__name__)


@dataclass(kw_only=True, slots=True, frozen=True)
class PublishScenarioToForumParams:
    game: dto.FullGame
    username: str
    password: str
    chat_id: int


@dataclass(kw_only=True, slots=True, frozen=True)
class PublishScenarioToForumTask:
    params: PublishScenarioToForumParams
    bot: Bot

    async def __call__(self) -> None:
        await upload(
            map_game_for_upload(self.params.game), self.params.username, self.params.password
        )
        await self.bot.send_message(
            chat_id=self.params.chat_id,
            text="Сценарий успешно загружен на форум",
        )


@dataclass(kw_only=True, slots=True, frozen=True)
class PublishScenarioToChannelParams:
    game: dto.FullGame
    game_stat: dto.GameStat
    keys: dict[dto.Team, list[dto.KeyTime]]
    channel_id: int
    manager: BaseDialogManager


@dataclass(kw_only=True, slots=True, frozen=True)
class PublishScenarioToChannelTask:
    params: PublishScenarioToChannelParams
    hint_sender: HintSender
    telegraph: Telegraph
    bot: Bot
    config: BotConfig

    async def __call__(self) -> None:
        game = self.params.game
        channel_id = self.params.channel_id
        publisher = GamePublisher(
            hint_sender=self.hint_sender,
            game=game,
            channel_id=channel_id,
            bot=self.bot,
            config=self.config,
            game_stat=self.params.game_stat,
            keys=self.params.keys,
            telegraph=self.telegraph,
        )
        started_msg_id = await publisher.publish_scn()
        results_msg_id = await publisher.publish_results()
        keys_msg_id = await publisher.publish_keys()
        table_of_content = (
            f"Начало сценария: {no_public_message_link(channel_id, started_msg_id)}\n"
            f"Результаты игры: {no_public_message_link(channel_id, results_msg_id)}\n"
            f"Лог ключей: {no_public_message_link(channel_id, keys_msg_id)}"
        )
        await self.bot.send_message(chat_id=channel_id, text=table_of_content)
        invite = await get_invite(channel_id=channel_id, bot=self.bot)

        text_invite_scn = f"Чтобы его увидеть, нужно войти в канал: {invite}"
        await self.bot.send_message(
            self.config.game_log_chat,
            f"Загружен сценарий игры {hd.bold(hd.quote(game.name))}.\n{text_invite_scn}",
        )
        await self.params.manager.update(
            {"text_invite": text_invite_scn + "\n" + table_of_content, "started": False}
        )
        author_chat_id = game.author.get_chat_id()
        if author_chat_id is None:
            logger.warning(
                "game %s author %s has no telegram chat, scenario link not sent",
                game.id,
                game.author.id,
            )
            return
        await self.bot.send_message(
            chat_id=author_chat_id,
            text=f"Сценарий загружен.\n{text_invite_scn}",
        )


@dataclass(kw_only=True, slots=True, frozen=True)
class SendLevelHintsParams:
    level: dto.Level
    chat_id: int


@dataclass(kw_only=True, slots=True, frozen=True)
class SendLevelHintsTask:
    params: SendLevelHintsParams
    hint_sender: HintSender

    async def __call__(self) -> None:
        publisher = LevelPublisher(
            hint_sender=self.hint_sender,
            level=self.params.level,
            chat_id=self.params.chat_id,
        )
        await publisher.publish()


@dataclass(kw_only=True, slots=True, frozen=True)
class FeedUpdateParams:
    update: dict[str, Any]
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True, slots=True, frozen=True)
class FeedUpdateTask:
    """Process one webhook update after the http response is already sent."""

    params: FeedUpdateParams
    bot: Bot
    dispatcher: Dispatcher

    async def __call__(self) -> None:
        result = await self.dispatcher.feed_raw_update(
            bot=self.bot, update=self.params.update, **self.params.data
        )
        if isinstance(result, TelegramMethod):
            await self.dispatcher.silent_call_request(bot=self.bot, result=result)


async def get_invite(channel_id: int, bot: Bot) -> str:
    channel = await bot.get_chat(channel_id)
    invite = channel.invite_link
    if not invite:
        invite = await bot.export_chat_invite_link(channel_id)

    return invite


def no_public_message_link(chat_id: int, message_id: int) -> str:
    return f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"


class BackgroundTasksProvider(Provider):
    scope = Scope.REQUEST

    publish_to_forum_params = from_context(PublishScenarioToForumParams)
    publish_to_forum = provide(PublishScenarioToForumTask)

    publish_to_channel_params = from_context(PublishScenarioToChannelParams)
    publish_to_channel = provide(PublishScenarioToChannelTask)

    send_level_hints_params = from_context(SendLevelHintsParams)
    send_level_hints = provide(SendLevelHintsTask)

    feed_update_params = from_context(FeedUpdateParams)
    feed_update = provide(FeedUpdateTask)
