import logging
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.markdown import html_decoration as hd

from shvatka.core.models import dto
from shvatka.core.views.team import (
    CaptainChanged,
    PlayerJoinedTeam,
    PlayerLeftTeam,
    TeamEvent,
    TeamNotifier,
)
from shvatka.tgbot.services.member_tags import MemberTagger
from shvatka.tgbot.views.player import get_emoji
from shvatka.tgbot.views.user import get_small_card, get_small_card_no_link

logger = logging.getLogger(__name__)


def render_team_players(
    team: dto.Team, players: Sequence[dto.FullTeamPlayer], *, notification: bool = False
) -> str:
    cap = team.captain
    cap_card = get_small_card_no_link(cap) if cap else "отсутствует"
    rez = f"🚩Команда: {hd.bold(hd.quote(team.name))}\n"
    rez += f"🔢ID{team.id}\n"
    rez += f"👑Капитан: {cap_card}\n"
    if team.description is not None:
        rez += f"📃Девиз: {hd.quote(team.description)}"
    rez += "Список игроков:\n"
    for team_player in players:
        rez += (
            f"{hd.quote(get_emoji(team_player))} "
            f"{get_small_card(team_player.player, notification=notification)}, "
            f"{hd.quote(team_player.role)}\n"
        )
    return rez


def render_leave_confirmation(
    player: dto.Player, team: dto.Team, *, chat_id: int, private: bool
) -> str | None:
    """What the bot says in the chat where ``/leave`` was typed.

    «Ты» is unambiguous only in a private chat — elsewhere the bot answers with a
    plain message, so the player has to be named. In the team's own chat there is
    nothing to add: :class:`BotTeamNotifier` already announces the leave there.
    """
    if private:
        return f"Ты вышел из команды {hd.quote(team.name)}"
    if team.get_chat_id() == chat_id:
        return None
    return f"Игрок {hd.quote(player.name_mention)} вышел из команды {hd.quote(team.name)}"


@dataclass
class BotTeamNotifier(TeamNotifier):
    bot: Bot
    tagger: MemberTagger

    async def notify(self, event: TeamEvent) -> None:
        await self._retag(event)
        await self._send_to_team_chat(event)

    async def _retag(self, event: TeamEvent) -> None:
        """Team membership defines the tag of the player in public chats."""
        match event:
            case PlayerJoinedTeam():
                await self.tagger.sync(event.invited, event.team)
            case PlayerLeftTeam():
                await self.tagger.sync(event.removed, None)

    async def _send_to_team_chat(self, event: TeamEvent) -> None:
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
                    return f"Игрок {hd.quote(event.invited.name_mention)} вступил в команду."
                return (
                    f"Игрок {hd.quote(event.invited.name_mention)} добавлен в команду "
                    f"(пригласил {hd.quote(event.actor.name_mention)})."
                )
            case PlayerLeftTeam():
                if event.by_self:
                    return f"Игрок {hd.quote(event.removed.name_mention)} вышел из команды."
                return (
                    f"Игрок {hd.quote(event.removed.name_mention)} удалён из команды "
                    f"(удалил {hd.quote(event.actor.name_mention)})."
                )
            case CaptainChanged():
                text = f"👑Новый капитан команды — {hd.quote(event.new_captain.name_mention)}."
                if not event.by_old_captain:
                    text += f" Капитанство передал {hd.quote(event.actor.name_mention)}."
                return text
            case _:
                return None
