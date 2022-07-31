import logging
import re

from aiogram import types, Dispatcher
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.dispatcher.filters import StateFilter, Command, CommandObject
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import any_state

logger = logging.getLogger(__name__)

YOU_ARE_IN_STATE_MSG = "Вы находитесь в диалоге (например в середине написания уровня, " \
                       "тестирования уровня и тому подобное). " \
                       "Если Вы не помните такого или не понимаете о чём речь - жмите /cancel"


async def message_in_state(message: types.Message, state: FSMContext, command: CommandObject):
    current_state = await state.get_state()
    if current_state is None:
        raise SkipHandler
    logger.info(
        'user %s with %s in %s send command %s',
        message.from_user.id,
        current_state,
        message.chat.id,
        command.command,
    )
    await message.reply(YOU_ARE_IN_STATE_MSG)


async def not_supported_callback(callback_query: types.CallbackQuery):
    await callback_query.answer(
        "Эта кнопка не поддерживается или не предназначена для Вас. хз где вы ее взяли",
        show_alert=True
    )
    logger.warning(
        "User {user} press unsupported button in query {query}",
        callback_query.from_user.id,
        callback_query.json(),
    )


async def callback_in_state(callback_query: types.CallbackQuery):
    logger.warning(
        "user {user} click {query} in state",
        callback_query.from_user.id,
        callback_query.data,
    )
    await callback_query.answer(YOU_ARE_IN_STATE_MSG, show_alert=True)
    await callback_query.message.answer(YOU_ARE_IN_STATE_MSG)


def setup_last_handlers(dp: Dispatcher):
    dp.message.register(message_in_state, Command(commands=re.compile('.*')))
    dp.callback_query.register(not_supported_callback)
    dp.callback_query.register(callback_in_state, StateFilter(state=any_state))
