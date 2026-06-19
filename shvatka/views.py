import logging
from dataclasses import dataclass
from typing import Iterable

from shvatka.api.utils.web_input import (
    WebGameView,
    WebTeamNotifier,
    WebOrgNotifier,
    WebGamePreparer,
    WebGameLogWriter,
)
from shvatka.core.interfaces.dal.game_play import GamePreparer
from shvatka.core.models import dto
from shvatka.core.models.dto import action
from shvatka.core.views.game import (
    GameView,
    GameViewPreparer,
    InputContainer,
    OrgNotifier,
    Event,
    GameLogWriter,
    GameLogEvent,
)
from shvatka.core.views.team import TeamNotifier, TeamEvent
from shvatka.tgbot.views.game import BotView, BotOrgNotifier, GameBotLog
from shvatka.tgbot.views.team import BotTeamNotifier

logger = logging.getLogger(__name__)


@dataclass
class ComplexOrgNotifier(OrgNotifier):
    bot: BotOrgNotifier
    web: WebOrgNotifier

    async def notify(self, event: Event) -> None:
        try:
            await self.bot.notify(event)
        except Exception as e:
            logger.exception("bot org notify error", exc_info=e)
        try:
            await self.web.notify(event)
        except Exception as e:
            logger.exception("web org notify error", exc_info=e)


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
        try:
            await self.bot.log(log_event)
        except Exception as e:
            logger.exception("bot game log error", exc_info=e)
        try:
            await self.web.log(log_event)
        except Exception as e:
            logger.exception("web game log error", exc_info=e)


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

    async def send_puzzle(self, team: dto.Team, level: dto.Level) -> None:
        try:
            await self.bot.send_puzzle(team=team, level=level)
        except Exception as e:
            logger.exception("bot send_puzzle error", exc_info=e)
        try:
            await self.web.send_puzzle(team=team, level=level)
        except Exception as e:
            logger.exception("web send_puzzle error", exc_info=e)

    async def send_hint(self, team: dto.Team, hint_number: int, level: dto.Level) -> None:
        try:
            await self.bot.send_hint(team=team, hint_number=hint_number, level=level)
        except Exception as e:
            logger.exception("bot send hint error", exc_info=e)
        try:
            await self.web.send_hint(team=team, hint_number=hint_number, level=level)
        except Exception as e:
            logger.exception("web send hint error", exc_info=e)

    async def duplicate_key(self, key: dto.KeyTime, input_container: InputContainer) -> None:
        try:
            await self.bot.duplicate_key(key=key, input_container=input_container)
        except Exception as e:
            logger.exception("bot duplicate_key error", exc_info=e)
        try:
            await self.web.duplicate_key(key=key, input_container=input_container)
        except Exception as e:
            logger.exception("web duplicate_key error", exc_info=e)

    async def wrong_key(self, key: dto.KeyTime, input_container: InputContainer) -> None:
        try:
            await self.bot.wrong_key(key=key, input_container=input_container)
        except Exception as e:
            logger.exception("bot wrong_key error", exc_info=e)
        try:
            await self.web.wrong_key(key=key, input_container=input_container)
        except Exception as e:
            logger.exception("web wrong_key error", exc_info=e)

    async def effects_key(
        self, key: dto.KeyTime, effects: action.Effects, input_container: InputContainer
    ) -> None:
        try:
            await self.bot.effects_key(key=key, effects=effects, input_container=input_container)
        except Exception as e:
            logger.exception("bot effects_key error", exc_info=e)
        try:
            await self.web.effects_key(key=key, effects=effects, input_container=input_container)
        except Exception as e:
            logger.exception("web effects_key error", exc_info=e)

    async def game_finished(self, team: dto.Team, input_container: InputContainer) -> None:
        try:
            await self.bot.game_finished(team=team, input_container=input_container)
        except Exception as e:
            logger.exception("bot game_finished error", exc_info=e)
        try:
            await self.web.game_finished(team=team, input_container=input_container)
        except Exception as e:
            logger.exception("web game_finished error", exc_info=e)

    async def game_finished_by_all(self, team: dto.Team) -> None:
        try:
            await self.bot.game_finished_by_all(team=team)
        except Exception as e:
            logger.exception("bot game_finished_by_all error", exc_info=e)
        try:
            await self.web.game_finished_by_all(team=team)
        except Exception as e:
            logger.exception("web game_finished_by_all error", exc_info=e)

    async def effects(
        self, team: dto.Team, effects: action.Effects, input_container: InputContainer
    ) -> None:
        try:
            await self.bot.effects(team=team, effects=effects, input_container=input_container)
        except Exception as e:
            logger.exception("bot effects error", exc_info=e)
        try:
            await self.web.effects(team=team, effects=effects, input_container=input_container)
        except Exception as e:
            logger.exception("web effects error", exc_info=e)
