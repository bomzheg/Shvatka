import logging
from collections.abc import Awaitable, Iterable, Sequence
from dataclasses import dataclass

from shvatka.api.app.utils.web_input import (
    WebGameLogWriter,
    WebGamePreparer,
    WebGameView,
    WebOrgNotifier,
    WebTeamNotifier,
)
from shvatka.core.interfaces.dal.game_play import GamePreparer
from shvatka.core.models import dto
from shvatka.core.views.game import (
    AnyViewTask,
    Event,
    GameLogEvent,
    GameLogWriter,
    GameView,
    GameViewPreparer,
    OrgNotifier,
)
from shvatka.core.views.team import TeamEvent, TeamNotifier
from shvatka.tgbot.views.game import BotOrgNotifier, BotView, GameBotLog
from shvatka.tgbot.views.team import BotTeamNotifier

logger = logging.getLogger(__name__)


async def show_on_both(*, bot: Awaitable[None], web: Awaitable[None]) -> None:
    """The site first: a push is one https call, telegram is minutes of them.

    A web failure is logged and the bot half still runs; a bot failure is left
    to the caller, which retries and alerts it.
    """
    try:
        await web
    except Exception as e:
        logger.exception("web view error", exc_info=e)
    await bot


@dataclass
class ComplexOrgNotifier(OrgNotifier):
    bot: BotOrgNotifier
    web: WebOrgNotifier

    async def notify(self, event: Event) -> None:
        await show_on_both(bot=self.bot.notify(event), web=self.web.notify(event))


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
    bot: GameBotLog
    web: WebGameLogWriter

    async def log(self, log_event: GameLogEvent) -> None:
        await show_on_both(bot=self.bot.log(log_event), web=self.web.log(log_event))


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
    bot: BotView
    web: WebGameView

    async def show(self, tasks: Sequence[AnyViewTask]) -> None:
        await show_on_both(bot=self.bot.show(tasks), web=self.web.show(tasks))
