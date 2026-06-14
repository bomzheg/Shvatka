import logging
from contextlib import suppress
from dataclasses import dataclass
from typing import Sequence

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.markdown import html_decoration as hd

from shvatka.core.models import dto
from shvatka.core.views.team import (
    PlayerJoinedTeam,
    PlayerLeftTeam,
    TeamEvent,
    TeamNotifier,
)
from shvatka.tgbot.views.player import get_emoji
from shvatka.tgbot.views.user import get_small_card_no_link, get_small_card

logger = logging.getLogger(__name__)


def render_team_card(team: dto.Team) -> str:
    cap = team.captain
    cap_card = get_small_card_no_link(cap) if cap else "отсутствует"
    rez = f"🚩Команда: {hd.bold(hd.quote(team.name))}\n"
    rez += f"🔢ID{team.id}\n"
    rez += f"👑Капитан: {cap_card}\n"
    if team.description is not None:
        rez += f"📃Девиз: {hd.quote(team.description)}"
    return rez


def render_team_players(
    team: dto.Team, players: Sequence[dto.FullTeamPlayer], *, notification: bool = False
) -> str:
    rez = f"Список игроков команды {hd.bold(hd.quote(team.name))}:\n"
    for team_player in players:
        rez += (
            f"{hd.quote(get_emoji(team_player))} "
            f"{get_small_card(team_player.player, notification=notification)}, "
            f"{hd.quote(team_player.role)}\n"
        )
    return rez


@dataclass
class BotTeamNotifier(TeamNotifier):
    bot: Bot

    async def notify(self, event: TeamEvent) -> None:
        if not event.team.has_chat():
            return
        chat_id = event.team.get_chat_id()
        if chat_id is None:
            return
        text = self._render(event)
        if text is None:
            return
        with suppress(TelegramAPIError):
            await self.bot.send_message(chat_id=chat_id, text=text)

    @staticmethod
    def _render(event: TeamEvent) -> str | None:
        match event:
            case PlayerJoinedTeam():
                if event.by_self:
                    return f"Игрок {hd.quote(event.player.name_mention)} вступил в команду."
                return (
                    f"Игрок {hd.quote(event.player.name_mention)} добавлен в команду "
                    f"(пригласил {hd.quote(event.inviter.name_mention)})."
                )
            case PlayerLeftTeam():
                if event.by_self:
                    return f"Игрок {hd.quote(event.player.name_mention)} вышел из команды."
                return (
                    f"Игрок {hd.quote(event.player.name_mention)} удалён из команды "
                    f"(капитан {hd.quote(event.remover.name_mention)})."
                )
            case _:
                return None
