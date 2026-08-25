"""Showing the game, after the request that decided to.

The combined app is the only place that knows both edges, so the tasks that
deliver to both live here rather than in ``tgbot`` or ``api``. Each is spawned
through the :class:`~shvatka.core.interfaces.nursery.Nursery` by the matching
``Complex*`` sender, and resolves what it sends through in its own di scope —
the request's is long closed by the time it runs.
"""

import logging
from collections.abc import Sequence

from dishka import FromDishka

from shvatka.api.app.utils.web_input import WebGameLogWriter, WebGameView, WebOrgNotifier
from shvatka.core.views.game import AnyViewTask, Event, GameLogEvent
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

    The site goes first: a push is one https call, while a puzzle in telegram
    is a caption and its hints a second apart. Each task is contained on its
    own — one chat the bot was thrown out of must not cost the others their
    puzzle.
    """
    for task in tasks:
        await deliver(lambda t=task: web.show([t]), alerter)  # type: ignore[misc]
    for task in tasks:
        await deliver(lambda t=task: bot.show([t]), alerter)  # type: ignore[misc]


async def notify_orgs(
    events: Sequence[Event],
    bot: FromDishka[BotOrgNotifier],
    web: FromDishka[WebOrgNotifier],
    alerter: FromDishka[BotAlert],
) -> None:
    for event in events:
        await deliver(lambda e=event: web.notify([e]), alerter)  # type: ignore[misc]
    for event in events:
        await deliver(lambda e=event: bot.notify([e]), alerter)  # type: ignore[misc]


async def write_game_log(
    log_events: Sequence[GameLogEvent],
    bot: FromDishka[GameBotLog],
    web: FromDishka[WebGameLogWriter],
    alerter: FromDishka[BotAlert],
) -> None:
    for log_event in log_events:
        await deliver(lambda e=log_event: web.log([e]), alerter)  # type: ignore[misc]
    for log_event in log_events:
        await deliver(lambda e=log_event: bot.log([e]), alerter)  # type: ignore[misc]
