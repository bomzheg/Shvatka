"""Nursery jobs that show the game on both edges.

Only the combined app knows both, so they live here rather than in ``tgbot`` or
``api``. Senders come from the job's own di scope: the request's is long closed.
"""

import asyncio
import logging
from collections.abc import Sequence

from dishka import FromDishka

from shvatka.api.app.utils.web_input import WebGameLogWriter, WebGameView, WebOrgNotifier
from shvatka.core.views.game import AnyViewTask, Event, GameLogEvent, group_by_team
from shvatka.tgbot.tasks import deliver
from shvatka.tgbot.views.bot_alert import BotAlert
from shvatka.tgbot.views.game import BotOrgNotifier, BotView, GameBotLog

logger = logging.getLogger(__name__)


async def show_game(
    tasks: Sequence[AnyViewTask],
    bot: FromDishka[BotView],
    web: FromDishka[WebGameView],
    alerter: FromDishka[BotAlert],
) -> None:
    """In order within a team; all teams at once, or a game start is teams × fan-out."""
    await asyncio.gather(
        *(_show_to_team(group, bot, web, alerter) for group in group_by_team(tasks))
    )


async def _show_to_team(
    tasks: Sequence[AnyViewTask], bot: BotView, web: WebGameView, alerter: BotAlert
) -> None:
    # the site first: a push is one https call, a puzzle is minutes of them
    for task in tasks:
        await deliver(lambda t=task: web.show([t]), alerter)  # type: ignore[misc]
    for task in tasks:
        await deliver(lambda t=task: bot.show([t]), alerter)  # type: ignore[misc]


async def notify_orgs(
    event: Event,
    bot: FromDishka[BotOrgNotifier],
    web: FromDishka[WebOrgNotifier],
    alerter: FromDishka[BotAlert],
) -> None:
    await deliver(lambda: web.notify(event), alerter)
    await deliver(lambda: bot.notify(event), alerter)


async def write_game_log(
    log_event: GameLogEvent,
    bot: FromDishka[GameBotLog],
    web: FromDishka[WebGameLogWriter],
    alerter: FromDishka[BotAlert],
) -> None:
    await deliver(lambda: web.log(log_event), alerter)
    await deliver(lambda: bot.log(log_event), alerter)
