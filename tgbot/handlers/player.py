from aiogram import Router, Bot, F
from aiogram.filters import Command, MagicData
from aiogram.types import Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, CallbackQuery
from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import save_promotion_confirm_invite, check_promotion_invite, \
    dismiss_promotion
from shvatka.utils.exceptions import SaltError
from tgbot import keyboards as kb
from tgbot.states import MainMenu
from tgbot.views.commands import START_COMMAND


async def main_menu(m: Message, dialog_manager: DialogManager):
    await dialog_manager.start(MainMenu.main)


async def send_promotion_invite(
    inline_query: InlineQuery, inline_data: kb.PromotePlayerID, player: dto.Player, dao: HolderDao,
):
    try:
        await check_promotion_invite(inviter=player, token=inline_data.token, dao=dao.secure_invite)
    except SaltError:
        return await inline_query.answer(
            results=[],
            switch_pm_text="Невозможно отправить, нажми сюда для подробностей.",
            switch_pm_parameter="wrong_invite"
        )
    token = await save_promotion_confirm_invite(player, dao.secure_invite)
    result = [
        InlineQueryResultArticle(
            id='1', title="Наделить полномочиями",
            description=f"Только людям, которых знаете лично!",
            input_message_content=InputTextMessageContent(
                message_text=(
                    "Получить полномочия автора? \n"
                    "Они нужны для написания и планирования игр."
                )
            ),
            reply_markup=kb.get_kb_agree_promotion(token=token, inviter=player)
        )
    ]
    await inline_query.answer(results=result, is_personal=True, cache_time=1)


async def dismiss_promotion_handler(c: CallbackQuery, callback_data: kb.AgreePromotionCD, dao: HolderDao, bot: Bot):
    await dismiss_promotion(callback_data.token, dao.secure_invite)
    await c.answer("правильно, большая сила - большая ответственность!", show_alert=True)
    await bot.edit_message_text(text="<i>(Игрок отказался от прав автора)</i>", inline_message_id=c.inline_message_id)


async def inviter_click_handler(c: CallbackQuery):
    await c.answer("ну и смысл?", cache_time=30)


def setup() -> Router:
    router = Router(name=__name__)
    router.message.register(main_menu, Command(START_COMMAND))
    router.inline_query.register(send_promotion_invite, kb.PromotePlayerID.filter())
    router.callback_query.register(
        inviter_click_handler, kb.AgreePromotionCD.filter(),
        MagicData(F.callback_data.inviter_id == F.player.id),
    )
    router.callback_query.register(dismiss_promotion_handler, kb.AgreePromotionCD.filter(~F.is_agreement))
    return router
