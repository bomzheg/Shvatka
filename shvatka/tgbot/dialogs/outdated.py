import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.manager.manager_middleware import MANAGER_KEY

from shvatka.core.interfaces.dal.player import TeamPlayerGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.players.player import get_full_team_player_or_none
from shvatka.core.utils.exceptions import PlayerNotInTeam
from shvatka.tgbot import states

logger = logging.getLogger(__name__)

NOT_IN_TEAM = "Ты больше не состоишь в команде. Окно устарело, открой меню заново"
NO_MORE_TEAMMATE = "Этот игрок больше не состоит в твоей команде. Окно устарело"


class DialogOutdated(Exception):
    def __init__(self, notify_user: str, text: str = "") -> None:
        super().__init__(text or notify_user)
        self.notify_user = notify_user
        self.text = text or notify_user


async def get_actual_team_player(identity: IdentityProvider) -> dto.FullTeamPlayer:
    try:
        return await identity.get_required_full_team_player()
    except PlayerNotInTeam as e:
        raise DialogOutdated(NOT_IN_TEAM, f"player {e.player_id} is not in a team anymore") from e


async def get_actual_teammate(
    teammate: dto.Player, team: dto.Team, dao: TeamPlayerGetter
) -> dto.FullTeamPlayer:
    team_player = await get_full_team_player_or_none(player=teammate, team=team, dao=dao)
    if team_player is None:
        raise DialogOutdated(
            NO_MORE_TEAMMATE, f"player {teammate.id} is not in team {team.id} anymore"
        )
    return team_player


class OutdatedDialogMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except DialogOutdated as e:
            logger.info("dialog is outdated: %s", e.text, exc_info=e)
            await self._notify(event, e)
            await self._restart(data.get(MANAGER_KEY))
            return None

    async def _notify(self, event: TelegramObject, e: DialogOutdated) -> None:
        if isinstance(event, CallbackQuery):
            await event.answer(e.notify_user, show_alert=True)
        elif isinstance(event, Message):
            await event.answer(e.notify_user)

    async def _restart(self, manager: DialogManager | None) -> None:
        if manager is None:
            return
        await manager.start(states.MainMenuSG.main, mode=StartMode.RESET_STACK)
