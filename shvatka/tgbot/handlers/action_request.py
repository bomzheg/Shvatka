from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka, inject

from shvatka.core.notifications.request_interactors import (
    AcceptRequestInteractor,
    DeclineRequestInteractor,
)
from shvatka.core.utils.exceptions import NotAuthorizedForAdmin, RequestNotPending
from shvatka.tgbot.keyboards.action_request import ActionRequestCD
from shvatka.tgbot.services.identity import TgBotIdentityProvider
from shvatka.tgbot.views.utils import total_remove_msg


@inject
async def resolve_action_request(
    callback: CallbackQuery,
    callback_data: ActionRequestCD,
    identity: FromDishka[TgBotIdentityProvider],
    accept_interactor: FromDishka[AcceptRequestInteractor],
    decline_interactor: FromDishka[DeclineRequestInteractor],
    bot: FromDishka[Bot],
) -> None:
    try:
        if callback_data.accept:
            await accept_interactor(identity=identity, request_id=callback_data.request_id)
            text = "Запрос принят"
        else:
            await decline_interactor(identity=identity, request_id=callback_data.request_id)
            text = "Запрос отклонён"
    except NotAuthorizedForAdmin:
        await callback.answer("Недостаточно прав, сорян", cache_time=3600)
        return
    except RequestNotPending:
        await callback.answer("Запрос уже обработан", show_alert=True)
        if callback.message is not None:
            await total_remove_msg(
                bot, chat_id=callback.message.chat.id, msg_id=callback.message.message_id
            )
        return
    if callback.message is not None:
        await total_remove_msg(
            bot, chat_id=callback.message.chat.id, msg_id=callback.message.message_id
        )
    await callback.answer(text)


def setup() -> Router:
    router = Router(name=__name__)
    router.callback_query.register(
        resolve_action_request, ActionRequestCD.filter(F.accept.in_({True, False}))
    )
    return router
