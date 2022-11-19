import logging

from aiogram import types, Router

from tgbot.filters import GameStatusFilter

logger = logging.getLogger(__name__)


async def not_supported_callback_on_running_game(callback_query: types.CallbackQuery):
    await callback_query.answer(
        "Эта кнопка не поддерживается во время игры. "
        "Попробуй ещё раз, когда все команды финишируют:)",
        show_alert=True
    )
    logger.warning(
        "User %s press unsupported button in query %s",
        callback_query.from_user.id,
        callback_query.json(),
    )


async def not_supported_callback(callback_query: types.CallbackQuery):
    await callback_query.answer(
        "Эта кнопка не поддерживается или не предназначена для Вас. хз где вы ее взяли",
        show_alert=True
    )
    logger.warning(
        "User %s press unsupported button in query %s",
        callback_query.from_user.id,
        callback_query.json(),
    )


def setup() -> Router:
    router = Router(name=__name__)
    router.callback_query.register(
        not_supported_callback_on_running_game,
        GameStatusFilter(running=True),
    )
    router.callback_query.register(not_supported_callback)
    return router
