"""Showing the game, after the request that decided to.

The combined app is the only place that knows both edges, so the tasks that
deliver to both live here rather than in ``tgbot`` or ``api``. Each is spawned
through the :class:`~shvatka.core.interfaces.nursery.Nursery` by the matching
``Complex*`` sender, and resolves what it sends through in its own di scope —
the request's is long closed by the time it runs.
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
    """Show one request's tasks on both edges, in the order they were decided.

    One team at a time within a team, every team at once across them: a game
    starting sends a puzzle to each of them, and doing that in turn would cost
    the last team the whole fan-out of all the others.

    Each task is contained on its own — one chat the bot was thrown out of must
    not cost the others their puzzle.
    """
    await asyncio.gather(
        *(_show_to_team(group, bot, web, alerter) for group in group_by_team(tasks))
    )


async def _show_to_team(
    tasks: Sequence[AnyViewTask], bot: BotView, web: WebGameView, alerter: BotAlert
) -> None:
    """The site first: a push is one https call, a puzzle is minutes of them."""
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
