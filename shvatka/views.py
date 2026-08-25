import logging
from dataclasses import dataclass
from typing import Iterable, Sequence

from shvatka.api.app.utils.web_input import WebGamePreparer, WebTeamNotifier
from shvatka.core.interfaces.dal.game_play import GamePreparer
from shvatka.core.models import dto
from shvatka.core.interfaces.nursery import Nursery
from shvatka.core.views.game import (
    AnyViewTask,
    GameView,
    GameViewPreparer,
    OrgNotifier,
    Event,
    GameLogWriter,
    GameLogEvent,
)
from shvatka.tasks import notify_orgs, show_game, write_game_log
from shvatka.core.views.team import TeamNotifier, TeamEvent
from shvatka.tgbot.views.game import BotView
from shvatka.tgbot.views.team import BotTeamNotifier

logger = logging.getLogger(__name__)


@dataclass
class ComplexOrgNotifier(OrgNotifier):
    """Tells the orgs on both edges, once the caller is done with them."""

    nursery: Nursery

    async def notify(self, event: Event) -> None:
        self.nursery.spawn(notify_orgs, event=event)


@dataclass
class ComplexGameViewPreparer(GameViewPreparer):
    bot: BotView
    web: WebGamePreparer

    async def prepare_game_view(
        self,
        game: dto.Game,
        teams: Iterable[dto.Team],
        orgs: Iterable[dto.Organizer],
        dao: GamePreparer,
    ) -> None:
        teams = list(teams)
        orgs = list(orgs)
        try:
            await self.bot.prepare_game_view(game, teams, orgs, dao)
        except Exception as e:
            logger.exception("bot prepare_game_view error", exc_info=e)
        try:
            await self.web.prepare_game_view(game, teams, orgs, dao)
        except Exception as e:
            logger.exception("web prepare_game_view error", exc_info=e)


@dataclass
class ComplexGameLogWriter(GameLogWriter):
    """Writes the game's public log on both edges, after the caller commits."""

    nursery: Nursery

    async def log(self, log_event: GameLogEvent) -> None:
        self.nursery.spawn(write_game_log, log_event=log_event)


@dataclass
class ComplexTeamNotifier(TeamNotifier):
    bot: BotTeamNotifier
    web: WebTeamNotifier

    async def notify(self, event: TeamEvent) -> None:
        try:
            await self.bot.notify(event)
        except Exception as e:
            logger.exception("bot team notify error", exc_info=e)
        try:
            await self.web.notify(event)
        except Exception as e:
            logger.exception("web team notify error", exc_info=e)


@dataclass
class ComplexView(GameView):
    """Shows the game on both edges — and never while the caller waits.

    By the time this is called the interactor has committed, so there is
    nothing left to fail: the tasks go to the nursery as one background job
    (:func:`~shvatka.tasks.show_game`) and the caller returns. A puzzle is a
    caption and several hints, a second apart; a player who typed a key must
    not wait for it, and neither must a scheduled job.

    One job for the whole list, so the messages of one request keep their
    order — a key is confirmed before the puzzle it opened. Between requests
    nothing is promised, and never was.
    """

    nursery: Nursery

    async def show(self, tasks: Sequence[AnyViewTask]) -> None:
        if tasks:
            self.nursery.spawn(show_game, tasks=tuple(tasks))
