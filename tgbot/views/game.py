from dataclasses import dataclass
from typing import Iterable

from aiogram import Bot

from shvatka.dal.game_play import GamePreparer
from shvatka.models import dto
from shvatka.models.dto.scn.time_hint import TimeHint
from shvatka.views.game import GameViewPreparer, GameView, GameLogWriter, OrgNotifier


@dataclass
class BotView(GameViewPreparer, GameView):
    bot: Bot

    async def prepare_game_view(
        self, game: dto.Game, teams: Iterable[dto.Team], orgs: Iterable[dto.Organizer], dao: GamePreparer,
    ) -> None:
        # TODO set bot commands for orgs, hide bot commands for players
        for team in teams:
            await self.bot.edit_message_reply_markup(
                chat_id=team.chat.tg_id,
                message_id=await dao.get_poll_msg(team=team, game=game),
                reply_markup=None,
            )

    async def send_puzzle(self, team: dto.Team, puzzle: TimeHint) -> None:
        pass

    async def send_hint(self, team: dto.Team, hint: TimeHint) -> None:
        pass

    async def duplicate_key(self, key: dto.KeyTime) -> None:
        pass

    async def correct_key(self, key: dto.KeyTime) -> None:
        pass

    async def wrong_key(self, key: dto.KeyTime) -> None:
        pass

    async def game_finished(self, team: dto.Team) -> None:
        pass

    async def game_finished_by_all(self, team: dto.Team) -> None:
        """todo change bot commands"""
        pass


@dataclass
class GameBotLog(GameLogWriter):
    bot: Bot
    log_chat_id: int

    async def log(self, message: str) -> None:
        pass


class BotOrgNotifier(OrgNotifier):
    bot: Bot

    async def notify(self, event) -> None:
        pass
