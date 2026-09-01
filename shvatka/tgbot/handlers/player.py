from contextlib import suppress

from aiogram import Bot, F, Router
from aiogram.enums import ChatType, InlineQueryResultType
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    LinkPreviewOptions,
    Message,
)
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog.api.protocols import BgManagerFactory
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.players.player import (
    agree_promotion,
    check_promotion_invite,
    dismiss_promotion,
    get_my_team,
    get_team_players,
    leave,
    save_promotion_confirm_invite,
)
from shvatka.core.utils.exceptions import SaltError, SaltNotExist
from shvatka.core.views.team import TeamNotifier
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import keyboards as kb
from shvatka.tgbot.filters.is_inviter import is_inviter
from shvatka.tgbot.utils.router import disable_router_on_game
from shvatka.tgbot.views.commands import LEAVE_COMMAND, PLAYERS_COMMAND, TEAM_COMMAND
from shvatka.tgbot.views.team import render_leave_confirmation, render_team_players


@inject
async def send_promotion_invite(
    inline_query: InlineQuery,
    inline_data: kb.PromotePlayerID,
    dao: FromDishka[HolderDao],
    identity: FromDishka[IdentityProvider],
):
    player = await identity.get_required_player()
    try:
        await check_promotion_invite(
            inviter=player, token=inline_data.token, dao=dao.secure_invite
        )
    except SaltError:
        await inline_query.answer(
            results=[],
            switch_pm_text="Невозможно отправить, нажми сюда для подробностей.",
            switch_pm_parameter="wrong_invite",
        )
        return
    token = await save_promotion_confirm_invite(player, dao.secure_invite)
    result = [
        InlineQueryResultArticle(
            type=InlineQueryResultType.ARTICLE,
            id="1",
            title="Наделить полномочиями",
            description="Только людям, которых знаете лично!",
            input_message_content=InputTextMessageContent(
                message_text="Получить аппрув?\nОн нужен для написания игр и создания команды"
            ),
            reply_markup=kb.get_kb_agree_promotion(token=token, inviter=player),
        )
    ]
    await inline_query.answer(
        results=result,  # type: ignore[arg-type]
        is_personal=True,
        cache_time=1,
    )


@inject
async def dismiss_promotion_handler(
    c: CallbackQuery,
    callback_data: kb.AgreePromotionCD,
    dao: FromDishka[HolderDao],
    bot: Bot,
    identity: FromDishka[IdentityProvider],
):
    player = await identity.get_required_player()
    with suppress(SaltNotExist):
        await dismiss_promotion(callback_data.token, dao.secure_invite)
    await c.answer("правильно, большая сила - большая ответственность!", show_alert=True)
    await bot.edit_message_text(
        text=f"<i>(Игрок {hd.quote(player.name_mention)} отказался от аппрува)</i>",
        inline_message_id=c.inline_message_id,
    )


@inject
async def agree_promotion_handler(
    c: CallbackQuery,
    callback_data: kb.AgreePromotionCD,
    dao: FromDishka[HolderDao],
    bot: Bot,
    identity: FromDishka[IdentityProvider],
    bg_manager_factory: FromDishka[BgManagerFactory],
):
    player = await identity.get_required_player()
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
        primary_chat_id: int = player.get_chat_id()  # type: ignore[assignment]
        bg = bg_manager_factory.bg(bot=bot, user_id=primary_chat_id, chat_id=primary_chat_id)
        await bg.update({})


async def inviter_click_handler(c: CallbackQuery):
    await c.answer("ну и смысл?", cache_time=30)


@inject
async def get_my_team_cmd(
    message: Message, identity: FromDishka[IdentityProvider], dao: FromDishka[HolderDao]
):
    team = await identity.get_team()
    if team:
        players = await get_team_players(team, dao.team_player)
        await message.answer(
            text=render_team_players(team=team, players=players, notification=True),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return
    await message.answer("Ты не состоишь в команде")


@inject
async def leave_handler(
    message: Message,
    dao: FromDishka[HolderDao],
    identity: FromDishka[IdentityProvider],
    team_notifier: FromDishka[TeamNotifier],
):
    player = await identity.get_required_player()
    team = await get_my_team(player, dao.team_player)
    if team is None:
        await message.reply("Ты не состоишь в команде")
        return
    await leave(player, player, dao.team_leaver, notifier=team_notifier)
    text = render_leave_confirmation(
        player,
        team,
        chat_id=message.chat.id,
        private=message.chat.type == ChatType.PRIVATE,
    )
    if text is not None:
        await message.reply(text)


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)

    router.inline_query.register(send_promotion_invite, kb.PromotePlayerID.filter())
    router.callback_query.register(
        inviter_click_handler,
        kb.AgreePromotionCD.filter(),
        is_inviter,
    )
    router.callback_query.register(
        dismiss_promotion_handler, kb.AgreePromotionCD.filter(~F.is_agreement)
    )
    router.callback_query.register(
        agree_promotion_handler, kb.AgreePromotionCD.filter(F.is_agreement)
    )

    router.message.register(
        get_my_team_cmd,
        Command(commands=[TEAM_COMMAND, PLAYERS_COMMAND]),
        F.chat.type == ChatType.PRIVATE,
    )
    router.message.register(leave_handler, Command(LEAVE_COMMAND))
    return router
