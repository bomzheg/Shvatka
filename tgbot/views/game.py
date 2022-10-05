from dataclasses import dataclass
from typing import Iterable

from aiogram import Bot

from shvatka.models import dto
from shvatka.models.dto.scn.time_hint import TimeHint
from shvatka.views.game import GameViewPreparer, GameView, GameLogWriter, OrgNotifier


@dataclass
class BotView(GameViewPreparer, GameView):
    bot: Bot

    async def prepare_game_view(
        self, game: dto.Game, teams: Iterable[dto.Team], orgs: Iterable[dto.Organizer],
    ):
        # TODO remove poll buttons
        # TODO set commands for orgs, hide commands for players
        pass

    async def send_puzzle(self, team: dto.Team, puzzle: TimeHint):
        pass


@dataclass
class GameBotLog(GameLogWriter):
    bot: Bot
    log_chat_id: int
    async def log(self, message: str): pass


class BotOrgNotifier(OrgNotifier):
    bot: Bot
    async def notify(self, event): pass
