from aiogram import Bot, Router, F
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.types import ChatJoinRequest, Message
from aiogram.utils.text_decorations import html_decoration as hd
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.models import dto
from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import states
from shvatka.tgbot.config.models.bot import BotConfig


@inject
async def chat_join_handler(
    chat_join_request: ChatJoinRequest,
    bot: Bot,
    config: FromDishka[BotConfig],
    holder_dao: FromDishka[HolderDao],
    state: FSMContext,
):
    instant_approve: bool = False
    try:
        user = await holder_dao.user.get_by_tg_id(chat_join_request.from_user.id)
        player = await holder_dao.player.get_by_user(user=user)
        team_player_history = await holder_dao.team_player.get_history(player)
        instant_approve = player.can_be_author or len(team_player_history) > 0
    except (exceptions.UserNotFoundError, exceptions.PlayerNotFoundError):
        pass
    if instant_approve:
        await bot.send_message(
            chat_id=chat_join_request.from_user.id,
            text=(
                f"Я впустил тебя в чат "
                f"{hd.quote(chat_join_request.chat.username or chat_join_request.chat.title)}"  # type: ignore[arg-type]
            ),
        )
        await bot.approve_chat_join_request(
            chat_id=chat_join_request.chat.id, user_id=chat_join_request.from_user.id
        )
    elif config.enabled_capcha:
        await state.set_state(states.CapchaSG.waiting_answer)
        await state.set_data({"requested_chat": chat_join_request.chat.id})
        await bot.send_message(
            chat_id=chat_join_request.from_user.id,
            text="В каком городе проходит Схватка? (не склоняется)",
        )


async def correct_answer(
    m: Message,
    user: dto.User,
    bot: Bot,
    state: FSMContext,
):
    assert m.text
    if "лыткарино" in m.text.lower():
        await bot.approve_chat_join_request(
            chat_id=(await state.get_data())["requested_chat"], user_id=user.tg_id
        )
        await m.answer("Верно! Вы допущены в чат. До встречи на игре")
        await state.clear()


def setup(config: BotConfig) -> Router:
    router = Router(name=__name__)
    router.chat_join_request.register(chat_join_handler, F.chat.id.in_(config.public_chats))
    router.message.register(
        correct_answer, F.chat.type == ChatType.PRIVATE, F.text, states.CapchaSG.waiting_answer
    )
    return router
