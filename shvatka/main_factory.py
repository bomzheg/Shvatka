import logging
from dataclasses import dataclass

from dishka import Provider, Scope, AsyncContainer, provide
from dishka.exceptions import NoContextValueError

from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.utils.web_input import WebGameView
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.dto import action
from shvatka.core.views.game import GameView, GameViewPreparer, InputContainer
from shvatka.tgbot.services.identity import TgBotIdentityProvider
from shvatka.tgbot.views.game import BotView

logger = logging.getLogger(__name__)


class ComplexOnlyProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def get_idp(self, container: AsyncContainer) -> IdentityProvider:
        try:
            return await container.get(TgBotIdentityProvider)
        except NoContextValueError:
            return await container.get(ApiIdentityProvider)

    @provide
    def complex_view(self, bot_view: BotView, web_view: WebGameView) -> GameView:
        return ComplexView(bot_view, web_view)

    @provide
    def complex_preparer(self, bot_view: BotView) -> GameViewPreparer:
        return bot_view


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


def get_complex_only_providers() -> list[Provider]:
    return [
        ComplexOnlyProvider(),
    ]
