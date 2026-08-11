from adaptix import Retort
from aiogram.dispatcher.middlewares.data import MiddlewareData
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import Stack, Context
from aiogram_dialog.context.storage import StorageProxy
from dishka import AsyncContainer

from shvatka.core.models import dto
from shvatka.infrastructure.db.dao.holder import HolderDao


class DialogMiddlewareData(MiddlewareData, total=False):
    dialog_manager: DialogManager
    aiogd_storage_proxy: StorageProxy
    aiogd_stack: Stack
    aiogd_context: Context


class SHMiddlewareData(DialogMiddlewareData, total=False):
    """
    Data every handler receives by name.

    Only what a lot of handlers need belongs here — anything else is requested
    from the container with ``FromDishka`` at the single place that uses it.
    """

    dishka_container: AsyncContainer
    retort: Retort
    dao: HolderDao
    user: dto.User | None
    chat: dto.Chat | None
    team: dto.Team | None
    player: dto.Player | None
    game: dto.Game | None
    team_player: dto.FullTeamPlayer | None
