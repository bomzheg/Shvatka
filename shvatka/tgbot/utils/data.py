from typing import TypedDict, Any

from adaptix import Retort
from aiogram import types, Bot, Router
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import Stack, Context
from aiogram_dialog.api.protocols import BgManagerFactory
from aiogram_dialog.context.storage import StorageProxy
from dataclass_factory import Factory
from dishka import AsyncContainer
from telegraph.aio import Telegraph

from shvatka.core.interfaces.clients.file_storage import FileStorage, FileGateway
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import GameLogWriter
from shvatka.core.views.level import LevelView
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.infrastructure.picture.results_painter import ResultsPainter
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.config.models.main import TgBotConfig
from shvatka.tgbot.username_resolver.user_getter import UserGetter
from shvatka.tgbot.views.hint_factory.hint_parser import HintParser
from shvatka.tgbot.views.hint_sender import HintSender


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
    main_config: TgBotConfig
    dishka_container: AsyncContainer
    user_getter: UserGetter
    dcf: Factory
    retort: Retort
    dao: HolderDao
    scheduler: Scheduler
    locker: KeyCheckerFactory
    file_storage: FileStorage
    telegraph: Telegraph
    hint_parser: HintParser
    file_gateway: FileGateway
    hint_sender: HintSender
    level_view: LevelView
    user: dto.User | None
    chat: dto.Chat | None
    team: dto.Team | None
    player: dto.Player | None
    game: dto.Game | None
    team_player: dto.FullTeamPlayer | None
    results_painter: ResultsPainter
    game_log: GameLogWriter
    bg_manager_factory: BgManagerFactory
