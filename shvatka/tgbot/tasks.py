import asyncio
import logging
import typing
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter, TelegramServerError
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import BaseDialogManager
from dishka import FromDishka
from telegraph.aio import Telegraph

from shvatka.core.interfaces.nursery import Nursery
from shvatka.core.models import dto
from shvatka.core.views.game import (
    AnyViewTask,
    GameLogWriter,
    GameView,
    OrgNotifier,
    ShowTasks,
    ViewSender,
    group_by_team,
)
from shvatka.infrastructure.crawler.game_scn.uploader.forum_scenario_uploader import upload
from shvatka.infrastructure.crawler.game_scn.uploader.game_mapper import map_game_for_upload
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.views.bot_alert import BotAlert
from shvatka.tgbot.views.hint_sender import HintSender
from shvatka.tgbot.views.results.rich import ResultsRichSender
from shvatka.tgbot.views.results.scenario import GamePublisher, LevelPublisher

logger = logging.getLogger(__name__)


DELIVERY_ATTEMPTS: typing.Final = 3
RETRY_BACKOFF: typing.Final = 1.0
MAX_RETRY_DELAY: typing.Final = 30.0
# what telegram may recover from on its own; everything else would fail the same
RETRIABLE_ERRORS: typing.Final = (TelegramRetryAfter, TelegramNetworkError, TelegramServerError)

Delivery = Callable[[], Awaitable[None]]


async def deliver(call: Delivery, alerter: BotAlert, what: str) -> None:
    try:
        await _with_retry(call, what)
    except Exception as e:
        logger.exception("cant deliver %s", what, exc_info=e)
        try:
            await alerter.alert(f"cant deliver {what} because of {e!s}")
        except Exception as alert_error:
            logger.exception("cant alert about failed delivery", exc_info=alert_error)


async def _with_retry(call: Delivery, what: str) -> None:
    for attempt in range(1, DELIVERY_ATTEMPTS + 1):
        try:
            await call()
        except RETRIABLE_ERRORS as e:  # retrying is the point of the loop
            delay = _retry_delay(e, attempt)
            if attempt == DELIVERY_ATTEMPTS or delay is None:
                raise
            logger.warning(
                "cant deliver %s (attempt %s of %s), retrying in %.1f s: %s",
                what,
                attempt,
                DELIVERY_ATTEMPTS,
                delay,
                e,
            )
            await asyncio.sleep(delay)
        else:
            return


def _retry_delay(error: Exception, attempt: int) -> float | None:
    if isinstance(error, TelegramRetryAfter):
        return float(error.retry_after) if error.retry_after <= MAX_RETRY_DELAY else None
    return RETRY_BACKOFF * 2 ** (attempt - 1)


@dataclass
class NurseryViewSender(ViewSender):
    nursery: Nursery

    async def show_later(self, tasks: ShowTasks) -> None:
        if tasks.view or tasks.org or tasks.log:
            self.nursery.spawn(show_game, tasks=tasks)


async def show_game(
    tasks: ShowTasks,
    view: FromDishka[GameView],
    org_notifier: FromDishka[OrgNotifier],
    game_log: FromDishka[GameLogWriter],
    alerter: FromDishka[BotAlert],
) -> None:
    await asyncio.gather(
        *(_show_to_team(group, view, alerter) for group in group_by_team(tasks.view))
    )
    for event in tasks.org:
        what = f"{type(event).__name__} to {len(event.orgs_list)} orgs"
        await deliver(lambda e=event: org_notifier.notify(e), alerter, what)  # type: ignore[misc]
    for log_event in tasks.log:
        what = f"game log {log_event.type.name}"
        await deliver(lambda e=log_event: game_log.log(e), alerter, what)  # type: ignore[misc]


async def _show_to_team(tasks: Sequence[AnyViewTask], view: GameView, alerter: BotAlert) -> None:
    for task in tasks:
        await deliver(lambda t=task: view.show([t]), alerter, _describe(task))  # type: ignore[misc]


def _describe(task: AnyViewTask) -> str:
    team = task.team
    return f"{type(task).__name__} to team {team.id} (chat {team.get_chat_id()})"


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
