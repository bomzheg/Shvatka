from typing import TypedDict, Any, NotRequired

from aiogram import types, Bot, Router
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import Stack, Context
from aiogram_dialog.context.storage import StorageProxy
from dataclass_factory import Factory
from telegraph.aio import Telegraph

from shvatka.core.interfaces.clients.file_storage import FileStorage, FileGateway
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser


class AiogramMiddlewareData(TypedDict, total=False):
    event_from_user: types.User
    event_chat: types.Chat
    bot: Bot
    fsm_storage: BaseStorage
    state: FSMContext
    raw_state: Any
    handler: HandlerObject
    event_update: types.Update
    event_router: Router


class DialogMiddlewareData(AiogramMiddlewareData, total=False):
    dialog_manager: DialogManager
    aiogd_storage_proxy: StorageProxy
    aiogd_stack: Stack
    aiogd_context: Context


class MiddlewareData(DialogMiddlewareData, total=False):
    config: BotConfig
    user_getter: UserGetter
    dcf: Factory
    dao: HolderDao
    scheduler: Scheduler
    locker: KeyCheckerFactory
    file_storage: FileStorage
    telegraph: Telegraph
    hint_parser: HintParser
    file_gateway: FileGateway
    user: dto.User
    chat: dto.Chat
    team: NotRequired[dto.Team]
    player: dto.Player
    game: dto.Game | None
    team_player: dto.FullTeamPlayer | None
