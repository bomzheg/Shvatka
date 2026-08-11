from aiogram import Dispatcher


from .bot_rights_middleware import BotRightsMiddleware
from .data_load_middleware import LoadDataMiddleware
from .fix_target_middleware import FixTargetMiddleware
from .init_middleware import InitMiddleware
from .load_team_player import TeamPlayerMiddleware


def setup_middlewares(dp: Dispatcher):
    dp.update.middleware(InitMiddleware())
    dp.update.middleware(LoadDataMiddleware())
    dp.message.middleware(FixTargetMiddleware())
    dp.my_chat_member.outer_middleware(BotRightsMiddleware())
