"""Guarding dialogs against state which changed while the window was waiting.

Telegram keeps an inline keyboard clickable forever, so a window rendered today
may get its button pressed in a month - by which time the captain has removed
the player from the team the window was built for. Nothing tells the dialog
that: `dialog_data` still holds the team id captured on start, and the getter
still believes the player is a member. Re-checking on every event is the only
option.

`DialogOutdated`, raised from a getter or a handler, is how a dialog says "what
I was opened for is gone". `OutdatedDialogMiddleware` catches it, tells the user
what happened and drops them back into the main menu, which is built out of
current data - instead of an `assert` blowing up or a window rendering around a
team that isn't there.
"""

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
    """The dialog was opened for state which no longer holds.

    Not an `SHError`: nothing went wrong in the domain, the user simply pressed
    a button of a window which reality has moved on from.
    """

    def __init__(self, notify_user: str, text: str = "") -> None:
        super().__init__(text or notify_user)
        self.notify_user = notify_user
        self.text = text or notify_user


async def get_actual_team_player(identity: IdentityProvider) -> dto.FullTeamPlayer:
    """The acting player's membership as it is right now, `.team` included.

    The window was rendered against whatever `IdentityProvider` answered back
    then; this asks it again, and turns "not in a team" from a domain error
    into "this window is stale".
    """
    try:
        return await identity.get_required_full_team_player()
    except PlayerNotInTeam as e:
        raise DialogOutdated(NOT_IN_TEAM, f"player {e.player_id} is not in a team anymore") from e


async def get_actual_teammate(
    teammate: dto.Player, team: dto.Team, dao: TeamPlayerGetter
) -> dto.FullTeamPlayer:
    """Membership of another player in `team`, as it is right now.

    Guards the "selected player" of the captain's bridge: by the time the
    captain presses a button the player may have left, or even joined another
    team - and acting on their current membership would touch the wrong team.
    `IdentityProvider` only knows the acting player, so this one takes the dao.
    """
    team_player = await get_full_team_player_or_none(player=teammate, team=team, dao=dao)
    if team_player is None:
        raise DialogOutdated(
            NO_MORE_TEAMMATE, f"player {teammate.id} is not in team {team.id} anymore"
        )
    return team_player


class OutdatedDialogMiddleware(BaseMiddleware):
    """Turns `DialogOutdated` into a notification and a fresh main menu.

    Installed as an inner middleware of the dialogs router, so it wraps every
    dialog handler - including the window getters, which run inside `show()`
    and therefore cannot end the dialog themselves.
    """

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
        """Drop the whole stack, not just the broken dialog.

        Whatever the dialogs below kept in their `dialog_data` was captured
        against the same state that just turned out to be gone, so returning
        into one of them only moves the problem one window down.
        """
        if manager is None:
            return
        await manager.start(states.MainMenuSG.main, mode=StartMode.RESET_STACK)
