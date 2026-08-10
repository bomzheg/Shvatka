"""Background tasks of the bot: work spawned through the app :class:`Nursery`.

Each task is a pair — a frozen params dataclass carrying the data of a single
run, and a class whose dependencies come from DI. The task runs in a scope of
its own, so it opens its own db session (and every other request-scoped
resource) rather than borrowing the handler's, which is gone by the time the
task starts.

Params carry ids, not entities: the task loads what it needs itself, on behalf
of the player who asked for it, so its authorization is checked in its own
scope instead of trusting whatever the handler happened to have in hand.
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

from shvatka.core.services.game import get_full_game
from shvatka.core.services.game_stat import get_game_stat, get_typed_keys
from shvatka.core.services.identity import PlayerIdentityProvider
from shvatka.core.services.level import get_by_id
from shvatka.infrastructure.crawler.game_scn.uploader.forum_scenario_uploader import upload
from shvatka.infrastructure.crawler.game_scn.uploader.game_mapper import map_game_for_upload
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.views.hint_sender import HintSender
from shvatka.tgbot.views.results.scenario import GamePublisher, LevelPublisher

logger = logging.getLogger(__name__)


@dataclass(kw_only=True, slots=True, frozen=True)
class PublishScenarioToForumParams:
    game_id: int
    player_id: int
    username: str
    password: str
    chat_id: int


@dataclass(kw_only=True, slots=True, frozen=True)
class PublishScenarioToForumTask:
    params: PublishScenarioToForumParams
    dao: HolderDao
    bot: Bot

    async def __call__(self) -> None:
        game = await get_full_game(
            id_=self.params.game_id,
            identity=await self._identity(),
            dao=self.dao.game,
        )
        await upload(map_game_for_upload(game), self.params.username, self.params.password)
        await self.bot.send_message(
            chat_id=self.params.chat_id,
            text="Сценарий успешно загружен на форум",
        )

    async def _identity(self) -> PlayerIdentityProvider:
        player = await self.dao.player.get_by_id(self.params.player_id)
        return PlayerIdentityProvider(player=player, dao=self.dao.organizer)


@dataclass(kw_only=True, slots=True, frozen=True)
class PublishScenarioToChannelParams:
    game_id: int
    player_id: int
    channel_id: int
    manager: BaseDialogManager


@dataclass(kw_only=True, slots=True, frozen=True)
class PublishScenarioToChannelTask:
    params: PublishScenarioToChannelParams
    dao: HolderDao
    hint_sender: HintSender
    telegraph: Telegraph
    bot: Bot
    config: BotConfig

    async def __call__(self) -> None:
        publisher = await self._build_publisher()
        started_msg_id = await publisher.publish_scn()
        results_msg_id = await publisher.publish_results()
        keys_msg_id = await publisher.publish_keys()
        channel_id = self.params.channel_id
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
            f"Загружен сценарий игры {hd.bold(hd.quote(publisher.game.name))}."
            f"\n{text_invite_scn}",
        )
        await self.params.manager.update(
            {"text_invite": text_invite_scn + "\n" + table_of_content, "started": False}
        )
        author_chat_id = publisher.game.author.get_chat_id()
        if author_chat_id is None:
            logger.warning(
                "game %s author %s has no telegram chat, scenario link not sent",
                publisher.game.id,
                publisher.game.author.id,
            )
            return
        await self.bot.send_message(
            chat_id=author_chat_id,
            text=f"Сценарий загружен.\n{text_invite_scn}",
        )

    async def _build_publisher(self) -> GamePublisher:
        player = await self.dao.player.get_by_id(self.params.player_id)
        identity = PlayerIdentityProvider(player=player, dao=self.dao.organizer)
        game = await get_full_game(id_=self.params.game_id, identity=identity, dao=self.dao.game)
        return GamePublisher(
            hint_sender=self.hint_sender,
            game=game,
            channel_id=self.params.channel_id,
            bot=self.bot,
            config=self.config,
            game_stat=await get_game_stat(game=game, identity=identity, dao=self.dao.game_stat),
            keys=await get_typed_keys(game=game, identity=identity, dao=self.dao.typed_keys),
            telegraph=self.telegraph,
        )


@dataclass(kw_only=True, slots=True, frozen=True)
class SendLevelHintsParams:
    level_id: int
    player_id: int


@dataclass(kw_only=True, slots=True, frozen=True)
class SendLevelHintsTask:
    params: SendLevelHintsParams
    dao: HolderDao
    hint_sender: HintSender

    async def __call__(self) -> None:
        author = await self.dao.player.get_by_id(self.params.player_id)
        chat_id = author.get_chat_id()
        if chat_id is None:
            logger.warning("player %s has no telegram chat, hints not sent", author.id)
            return
        level = await get_by_id(self.params.level_id, author, self.dao.level)
        publisher = LevelPublisher(hint_sender=self.hint_sender, level=level, chat_id=chat_id)
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
