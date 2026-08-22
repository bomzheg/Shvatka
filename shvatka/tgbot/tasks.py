"""Background tasks of the bot: work spawned through the app :class:`Nursery`.

A task is an ordinary async function. Its plain parameters are the data of one
run, passed to :meth:`Nursery.spawn`; its ``FromDishka[...]`` parameters are
resolved in the fresh scope the nursery opens for it, so the session-bound
things it works with (a :class:`HintSender` and its dao, for one) are acquired
and finalized by that scope rather than borrowed from the handler's, which is
gone by the time the task starts.

Entities travel as arguments: they are plain dataclasses, detached from any
session, so handing a loaded game or level to a task is free. What must never
cross is a resource tied to the caller's scope — a dao, a session, a sender —
those are what ``FromDishka`` is for.
"""

import logging
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from aiogram import Bot
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import BaseDialogManager
from dishka import FromDishka
from telegraph.aio import Telegraph

from shvatka.core.models import dto
from shvatka.infrastructure.crawler.game_scn.uploader.forum_scenario_uploader import upload
from shvatka.infrastructure.crawler.game_scn.uploader.game_mapper import map_game_for_upload
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.views.bot_alert import BotAlert
from shvatka.tgbot.views.game import BotOrgNotifier, BotView, GameBotLog
from shvatka.tgbot.views.hint_sender import HintSender
from shvatka.tgbot.views.results.rich import ResultsRichSender
from shvatka.tgbot.views.results.scenario import GamePublisher, LevelPublisher

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class BotSenders:
    """Everything the bot shows the game through, resolved in the task's scope."""

    view: BotView
    org_notifier: BotOrgNotifier
    game_log: GameBotLog


BotDelivery = Callable[[BotSenders], Awaitable[None]]
"""One recorded bot-side view call, waiting for the senders to run against."""


async def deliver_bot_views(
    calls: Sequence[BotDelivery],
    view: FromDishka[BotView],
    org_notifier: FromDishka[BotOrgNotifier],
    game_log: FromDishka[GameBotLog],
    alerter: FromDishka[BotAlert],
) -> None:
    """Show in telegram what one request decided to show, after it answered.

    The calls were recorded by :class:`~shvatka.tgbot.views.outbox.BotOutbox`
    during the request and are replayed here in the order they were made — a
    key is confirmed before the puzzle it opened. Only the order *within* one
    request is kept: two players of a team typing at once are two tasks, and
    their messages interleave exactly as they did when the request sent them
    itself.

    A failure is not the caller's problem anymore (it is long gone), so each
    call is contained on its own — one chat that can't be written to must not
    swallow the rest — and alerted, because nobody is watching the response
    for it.
    """
    senders = BotSenders(view=view, org_notifier=org_notifier, game_log=game_log)
    for call in calls:
        await _deliver_one(call, senders, alerter)


async def _deliver_one(call: BotDelivery, senders: BotSenders, alerter: BotAlert) -> None:
    try:
        await call(senders)
    except Exception as e:
        logger.exception("cant deliver bot view", exc_info=e)
        try:
            await alerter.alert(f"cant deliver bot view because of {e!s}")
        except Exception as alert_error:
            logger.error("cant alert about failed delivery", exc_info=alert_error)


async def publish_scenario_to_forum(
    game: dto.FullGame,
    username: str,
    password: str,
    chat_id: int,
    bot: FromDishka[Bot],
) -> None:
    await upload(map_game_for_upload(game), username, password)
    await bot.send_message(chat_id=chat_id, text="Сценарий успешно загружен на форум")


async def publish_scenario_to_channel(
    game: dto.FullGame,
    game_stat: dto.GameStat,
    keys: dict[dto.Team, list[dto.KeyTime]],
    channel_id: int,
    manager: BaseDialogManager,
    hint_sender: FromDishka[HintSender],
    telegraph: FromDishka[Telegraph],
    bot: FromDishka[Bot],
    config: FromDishka[BotConfig],
    results_sender: FromDishka[ResultsRichSender],
) -> None:
    publisher = GamePublisher(
        hint_sender=hint_sender,
        game=game,
        channel_id=channel_id,
        bot=bot,
        config=config,
        game_stat=game_stat,
        keys=keys,
        telegraph=telegraph,
        results_sender=results_sender,
    )
    started_msg_id = await publisher.publish_scn()
    results_msg_id = await publisher.publish_results()
    keys_msg_id = await publisher.publish_keys()
    table_of_content = (
        f"Начало сценария: {no_public_message_link(channel_id, started_msg_id)}\n"
        f"Результаты игры: {no_public_message_link(channel_id, results_msg_id)}\n"
        f"Лог ключей: {no_public_message_link(channel_id, keys_msg_id)}"
    )
    await bot.send_message(chat_id=channel_id, text=table_of_content)
    invite = await get_invite(channel_id=channel_id, bot=bot)

    text_invite_scn = f"Чтобы его увидеть, нужно войти в канал: {invite}"
    await bot.send_message(
        config.game_log_chat,
        f"Загружен сценарий игры {hd.bold(hd.quote(game.name))}.\n{text_invite_scn}",
    )
    await manager.update(
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
    await bot.send_message(
        chat_id=author_chat_id,
        text=f"Сценарий загружен.\n{text_invite_scn}",
    )


async def send_level_hints(
    level: dto.Level,
    chat_id: int,
    hint_sender: FromDishka[HintSender],
) -> None:
    publisher = LevelPublisher(hint_sender=hint_sender, level=level, chat_id=chat_id)
    await publisher.publish()


async def get_invite(channel_id: int, bot: Bot) -> str:
    channel = await bot.get_chat(channel_id)
    invite = channel.invite_link
    if not invite:
        invite = await bot.export_chat_invite_link(channel_id)

    return invite


def no_public_message_link(chat_id: int, message_id: int) -> str:
    return f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"
