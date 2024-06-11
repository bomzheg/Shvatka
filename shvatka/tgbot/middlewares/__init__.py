from aiogram import Dispatcher
from aiogram_dialog.api.protocols import BgManagerFactory
from dishka import AsyncContainer


from .data_load_middleware import LoadDataMiddleware
from .fix_target_middleware import FixTargetMiddleware
from .init_middleware import InitMiddleware
from .load_team_player import TeamPlayerMiddleware


def setup_middlewares(
    dp: Dispatcher,
    bg_manager_factory: BgManagerFactory,
):
    dp.update.middleware(InitMiddleware(bg_manager_factory=bg_manager_factory))
    dp.update.middleware(LoadDataMiddleware())
    dp.message.middleware(FixTargetMiddleware())
