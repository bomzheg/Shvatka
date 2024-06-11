from aiogram import Router, F, Bot
from aiogram.enums import InlineQueryResultType
from aiogram.filters import MagicData
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    CallbackQuery,
)
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram_dialog.api.protocols import BgManagerFactory
from dishka import FromDishka
from dishka.integrations.aiogram import inject

from shvatka.core.models import dto
from shvatka.core.services.game import get_game
from shvatka.core.services.organizers import (
    check_allow_manage_orgs,
    save_invite_to_orgs,
    dismiss_to_be_org,
    agree_to_be_org,
    check_game_token,
)
from shvatka.core.views.game import OrgNotifier
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import keyboards as kb
from shvatka.tgbot.utils.router import disable_router_on_game


async def invite_org_inline_query(
    q: InlineQuery,
    inline_data: kb.AddGameOrgID,
    player: dto.Player,
    dao: HolderDao,
):
    game = await get_game(id_=inline_data.game_id, dao=dao.game)
    check_game_token(game, inline_data.game_manage_token)
    check_allow_manage_orgs(game, player.id)
    token = await save_invite_to_orgs(game=game, inviter=player, dao=dao.secure_invite)
    result = [
        InlineQueryResultArticle(
            type=InlineQueryResultType.ARTICLE,
            id="1",
            title="Добавить в организаторы",
            description=f"Игра {game.name}",
            input_message_content=InputTextMessageContent(
                message_text=(
                    f"Стать со-организатором игры {game.name}?\n"
                    "В случае согласия будет невозможно сыграть в эту игру."
                )
            ),
            reply_markup=kb.get_kb_agree_be_org(token=token, inviter=player),
        )
    ]
    await q.answer(results=result, is_personal=True, cache_time=1)


async def dismiss_to_be_org_handler(
    c: CallbackQuery,
    callback_data: kb.AgreeBeOrgCD,
    player: dto.Player,
    dao: HolderDao,
    bot: Bot,
):
    await dismiss_to_be_org(callback_data.token, dao.secure_invite)
    await c.answer("правильно, лучше поиграть!", show_alert=True)
    await bot.edit_message_text(
        text=f"<i>(Игрок {hd.quote(player.name_mention)}  отказался от приглашения)</i>",
        inline_message_id=c.inline_message_id,
    )


@inject
async def agree_to_be_org_handler(
    c: CallbackQuery,
    callback_data: kb.AgreeBeOrgCD,
    player: dto.Player,
    dao: FromDishka[HolderDao],
    bot: FromDishka[Bot],
    org_notifier: FromDishka[OrgNotifier],
    bg_manager_factory: BgManagerFactory,
):
    await c.answer()
    await agree_to_be_org(
        token=callback_data.token,
        inviter_id=callback_data.inviter_id,
        player=player,
        org_notifier=org_notifier,
        dao=dao.org_adder,
    )
    await bot.edit_message_text(
        text=f"<i>(Игрок {hd.quote(player.name_mention)} принял приглашение)</i>",
        inline_message_id=c.inline_message_id,
    )
    primary_chat_id = player.get_chat_id()
    bg = bg_manager_factory.bg(bot=bot, user_id=primary_chat_id, chat_id=primary_chat_id)
    await bg.update({})


async def inviter_click_handler(c: CallbackQuery):
    await c.answer("ну и смысл?", cache_time=30)


def setup() -> Router:
    router = Router(name=__name__)
    disable_router_on_game(router)

    router.inline_query.register(invite_org_inline_query, kb.AddGameOrgID.filter())
    router.callback_query.register(
        inviter_click_handler,
        kb.AgreeBeOrgCD.filter(),
        MagicData(F.callback_data.inviter_id == F.player.id),
    )
    router.callback_query.register(
        dismiss_to_be_org_handler, kb.AgreeBeOrgCD.filter(~F.is_agreement)
    )
    router.callback_query.register(agree_to_be_org_handler, kb.AgreeBeOrgCD.filter(F.is_agreement))
    return router
