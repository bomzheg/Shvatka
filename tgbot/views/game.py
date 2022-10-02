from dataclasses import dataclass
from typing import Iterable

from aiogram import Bot

from shvatka.models import dto
from shvatka.views.game import GameViewPreparer


@dataclass
class GameBotViewPreparer(GameViewPreparer):
    bot: Bot

    async def prepare_game_view(
        self, game: dto.Game, teams: Iterable[dto.Team], orgs: Iterable[dto.Organizer],
    ):
        # TODO remove poll buttons
        # TODO set commands for orgs, hide commands for players
        pass
