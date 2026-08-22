import logging
from dataclasses import dataclass
from typing import Iterable

from shvatka.api.app.utils.web_input import (
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
from shvatka.tgbot.views.game import BotView
from shvatka.tgbot.views.outbox import BotOutbox
from shvatka.tgbot.views.team import BotTeamNotifier

logger = logging.getLogger(__name__)


@dataclass
class ComplexOrgNotifier(OrgNotifier):
    outbox: BotOutbox
    web: WebOrgNotifier

    async def notify(self, event: Event) -> None:
        self.outbox.add(lambda senders: senders.org_notifier.notify(event))
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
    outbox: BotOutbox
    web: WebGameLogWriter

    async def log(self, log_event: GameLogEvent) -> None:
        self.outbox.add(lambda senders: senders.game_log.log(log_event))
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
    """The game as both edges show it: the site now, telegram right after.

    The web half runs inline — it fills the container the http response is
    built from and sends a push, both of which the caller is waiting for. The
    bot half is only recorded (see :class:`~shvatka.tgbot.views.outbox.BotOutbox`):
    a chat full of hints, a second apart, is not something a player submitting
    a key should wait for.
    """

    outbox: BotOutbox
    web: WebGameView

    async def send_puzzle(self, team: dto.Team, level: dto.Level) -> None:
        self.outbox.add(lambda senders: senders.view.send_puzzle(team=team, level=level))
        try:
            await self.web.send_puzzle(team=team, level=level)
        except Exception as e:
            logger.exception("web send_puzzle error", exc_info=e)

    async def send_hint(self, team: dto.Team, hint_number: int, level: dto.Level) -> None:
        self.outbox.add(
            lambda senders: senders.view.send_hint(team=team, hint_number=hint_number, level=level)
        )
        try:
            await self.web.send_hint(team=team, hint_number=hint_number, level=level)
        except Exception as e:
            logger.exception("web send hint error", exc_info=e)

    async def duplicate_key(self, key: dto.KeyTime, input_container: InputContainer) -> None:
        self.outbox.add(
            lambda senders: senders.view.duplicate_key(key=key, input_container=input_container)
        )
        try:
            await self.web.duplicate_key(key=key, input_container=input_container)
        except Exception as e:
            logger.exception("web duplicate_key error", exc_info=e)

    async def wrong_key(self, key: dto.KeyTime, input_container: InputContainer) -> None:
        self.outbox.add(
            lambda senders: senders.view.wrong_key(key=key, input_container=input_container)
        )
        try:
            await self.web.wrong_key(key=key, input_container=input_container)
        except Exception as e:
            logger.exception("web wrong_key error", exc_info=e)

    async def effects_key(
        self, key: dto.KeyTime, effects: action.Effects, input_container: InputContainer
    ) -> None:
        self.outbox.add(
            lambda senders: senders.view.effects_key(
                key=key, effects=effects, input_container=input_container
            )
        )
        try:
            await self.web.effects_key(key=key, effects=effects, input_container=input_container)
        except Exception as e:
            logger.exception("web effects_key error", exc_info=e)

    async def game_finished(self, team: dto.Team, input_container: InputContainer) -> None:
        self.outbox.add(
            lambda senders: senders.view.game_finished(team=team, input_container=input_container)
        )
        try:
            await self.web.game_finished(team=team, input_container=input_container)
        except Exception as e:
            logger.exception("web game_finished error", exc_info=e)

    async def game_finished_by_all(self, team: dto.Team) -> None:
        self.outbox.add(lambda senders: senders.view.game_finished_by_all(team=team))
        try:
            await self.web.game_finished_by_all(team=team)
        except Exception as e:
            logger.exception("web game_finished_by_all error", exc_info=e)

    async def effects(
        self, team: dto.Team, effects: action.Effects, input_container: InputContainer
    ) -> None:
        self.outbox.add(
            lambda senders: senders.view.effects(
                team=team, effects=effects, input_container=input_container
            )
        )
        try:
            await self.web.effects(team=team, effects=effects, input_container=input_container)
        except Exception as e:
            logger.exception("web effects error", exc_info=e)
