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

import asyncio
import logging
import typing
from collections.abc import Awaitable, Callable

from aiogram import Bot
from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter, TelegramServerError
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import BaseDialogManager
from dishka import FromDishka
from telegraph.aio import Telegraph

from shvatka.core.models import dto
from shvatka.infrastructure.crawler.game_scn.uploader.forum_scenario_uploader import upload
from shvatka.infrastructure.crawler.game_scn.uploader.game_mapper import map_game_for_upload
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.views.bot_alert import BotAlert
from shvatka.tgbot.views.hint_sender import HintSender
from shvatka.tgbot.views.results.rich import ResultsRichSender
from shvatka.tgbot.views.results.scenario import GamePublisher, LevelPublisher

logger = logging.getLogger(__name__)


DELIVERY_ATTEMPTS: typing.Final = 3
"""How many times a deferred call is tried before it is given up on."""

RETRY_BACKOFF: typing.Final = 1.0
"""Seconds before the second attempt; doubled for each one after it."""

MAX_RETRY_DELAY: typing.Final = 30.0
"""A wait longer than this is not worth it — the game has moved on by then."""

RETRIABLE_ERRORS: typing.Final = (TelegramRetryAfter, TelegramNetworkError, TelegramServerError)
"""Failures telegram may recover from on its own; everything else is ours."""

Delivery = Callable[[], Awaitable[None]]
"""Showing one thing, ready to run — everything it needs is already bound."""


async def deliver(call: Delivery, alerter: BotAlert) -> None:
    """Run one deferred send, contained and shouted about if it fails.

    Nothing is watching a background delivery, so a failure has nowhere to go
    but an alert — and it must not take the rest of the batch with it.
    """
    try:
        await _with_retry(call)
    except Exception as e:
        logger.exception("cant deliver", exc_info=e)
        try:
            await alerter.alert(f"cant deliver because of {e!s}")
        except Exception as alert_error:
            logger.error("cant alert about failed delivery", exc_info=alert_error)


async def _with_retry(call: Delivery) -> None:
    """Try again when telegram says the failure was its own fault.

    Only failures a second attempt can fix are retried: being blocked by a chat
    or sending something malformed would fail identically forever.

    A call can be several messages (a puzzle is a caption and its hints), and a
    retry starts it from the beginning — so a failure halfway through resends
    what already arrived. That is deliberate: a duplicated puzzle is confusing,
    a half-sent one leaves the team stuck with nothing to solve.
    """
    for attempt in range(1, DELIVERY_ATTEMPTS + 1):
        try:
            await call()
        except RETRIABLE_ERRORS as e:  # noqa: PERF203  # retrying is the point of the loop
            delay = _retry_delay(e, attempt)
            if attempt == DELIVERY_ATTEMPTS or delay is None:
                raise
            logger.warning(
                "delivery failed (attempt %s of %s), retrying in %.1f s: %s",
                attempt,
                DELIVERY_ATTEMPTS,
                delay,
                e,
            )
            await asyncio.sleep(delay)
        else:
            return


def _retry_delay(error: Exception, attempt: int) -> float | None:
    """How long to wait before trying again, or ``None`` to stop trying."""
    if isinstance(error, TelegramRetryAfter):
        # telegram said exactly how long it wants to be left alone
        return float(error.retry_after) if error.retry_after <= MAX_RETRY_DELAY else None
    return RETRY_BACKOFF * 2 ** (attempt - 1)


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
