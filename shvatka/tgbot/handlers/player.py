from contextlib import suppress

from aiogram import Router, Bot, F
from aiogram.enums import ChatType, InlineQueryResultType
from aiogram.filters import Command, MagicData
from aiogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    CallbackQuery,
)
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog import StartMode, DialogManager

from shvatka.core.models import dto
from shvatka.core.services.player import (
    save_promotion_confirm_invite,
    check_promotion_invite,
    dismiss_promotion,
    agree_promotion,
    get_my_team,
    leave,
)
from shvatka.core.utils.exceptions import SaltError, SaltNotExist
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import keyboards as kb
from shvatka.tgbot import states
from shvatka.tgbot.utils.router import disable_router_on_game, register_start_handler
from shvatka.tgbot.views.commands import START_COMMAND, TEAM_COMMAND, LEAVE_COMMAND
from shvatka.tgbot.views.team import render_team_card


async def send_promotion_invite(
    inline_query: InlineQuery,
    inline_data: kb.PromotePlayerID,
    player: dto.Player,
    dao: HolderDao,
):
    try:
        await check_promotion_invite(
            inviter=player, token=inline_data.token, dao=dao.secure_invite
        )
    except SaltError:
        return await inline_query.answer(
            results=[],
            switch_pm_text="Невозможно отправить, нажми сюда для подробностей.",
            switch_pm_parameter="wrong_invite",
        )
    token = await save_promotion_confirm_invite(player, dao.secure_invite)
    result = [
        InlineQueryResultArticle(
            type=InlineQueryResultType.ARTICLE,
            id="1",
            title="Наделить полномочиями",
            description="Только людям, которых знаете лично!",
            input_message_content=InputTextMessageContent(
                message_text=("Получить аппрув?\nОн нужен для написания игр и создания команды")
            ),
            reply_markup=kb.get_kb_agree_promotion(token=token, inviter=player),
        )
    ]
    await inline_query.answer(results=result, is_personal=True, cache_time=1)


async def dismiss_promotion_handler(
    c: CallbackQuery,
    callback_data: kb.AgreePromotionCD,
    player: dto.Player,
    dao: HolderDao,
    bot: Bot,
):
    with suppress(SaltNotExist):
        await dismiss_promotion(callback_data.token, dao.secure_invite)
    await c.answer("правильно, большая сила - большая ответственность!", show_alert=True)
    await bot.edit_message_text(
        text=f"<i>(Игрок {hd.quote(player.name_mention)} отказался от аппрува)</i>",
        inline_message_id=c.inline_message_id,
    )


async def agree_promotion_handler(
    c: CallbackQuery,
    callback_data: kb.AgreePromotionCD,
    player: dto.Player,
    dao: HolderDao,
    bot: Bot,
    dialog_manager: DialogManager,
):
    await c.answer()
    try:
        await agree_promotion(
            token=callback_data.token,
            inviter_id=callback_data.inviter_id,
            target=player,
            dao=dao.player_promoter,
        )
    except SaltNotExist:
        await bot.edit_message_text(
            text="Приглашение устарело, отправьте его заново",
            inline_message_id=c.inline_message_id,
        )
    else:
        await bot.edit_message_text(
            text=(
                f"Успешно. Теперь игрок {hd.quote(player.name_mention)} "
                f"может самостоятельно писать игры и создавать команды"
            ),
            inline_message_id=c.inline_message_id,
        )
        primary_chat_id = player.get_chat_id()
        bg = dialog_manager.bg(user_id=primary_chat_id, chat_id=primary_chat_id)
        await bg.update({})


async def inviter_click_handler(c: CallbackQuery):
    await c.answer("ну и смысл?", cache_time=30)


async def get_my_team_cmd(message: Message, player: dto.Player, dao: HolderDao):
    team = await get_my_team(player, dao.team_player)
    if team:
        return await message.answer(
            text=render_team_card(team),
            disable_web_page_preview=True,
        )
    await message.answer("Ты не состоишь в команде")


async def leave_handler(message: Message, player: dto.Player, dao: HolderDao, bot: Bot):
    team = await get_my_team(player, dao.team_player)
    if team is None:
        return await message.answer("Ты не состоишь в команде")
    await leave(player, player, dao.team_leaver)
    await message.answer(f"Ты вышел из команды {hd.quote(team.name)}")
    await bot.send_message(
        chat_id=team.get_chat_id(),
        text=f"Игрок {hd.quote(player.name_mention)} вышел из команды.",
    )


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)

    register_start_handler(
        Command(START_COMMAND),
        state=states.MainMenuSG.main,
        router=router,
        mode=StartMode.RESET_STACK,
    )
    router.inline_query.register(send_promotion_invite, kb.PromotePlayerID.filter())
    router.callback_query.register(
        inviter_click_handler,
        kb.AgreePromotionCD.filter(),
        MagicData(F.callback_data.inviter_id == F.player.id),
    )
    router.callback_query.register(
        dismiss_promotion_handler, kb.AgreePromotionCD.filter(~F.is_agreement)
    )
    router.callback_query.register(
        agree_promotion_handler, kb.AgreePromotionCD.filter(F.is_agreement)
    )

    router.message.register(
        get_my_team_cmd, Command(TEAM_COMMAND), F.chat.type == ChatType.PRIVATE
    )
    router.message.register(leave_handler, Command(LEAVE_COMMAND))
    return router
