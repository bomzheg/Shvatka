from aiogram import Router, F, Bot
from aiogram.filters import MagicData
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, CallbackQuery

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.game import get_game
from shvatka.services.organizers import check_allow_add_orgs, save_invite_to_orgs, dismiss_to_be_org
from tgbot import keyboards as kb


async def invite_org_inline_query(q: InlineQuery, inline_data: kb.AddGameOrgID, player: dto.Player, dao: HolderDao):
    game = await get_game(id_=inline_data.game_id, dao=dao.game)
    check_allow_add_orgs(game, inline_data.game_manage_token, player)
    token = await save_invite_to_orgs(game=game, inviter=player, dao=dao.secure_invite)
    result = [
        InlineQueryResultArticle(
            id='1', title="Добавить в организаторы",
            description=f"Игра {game.name}",
            input_message_content=InputTextMessageContent(
                message_text=(
                    f"Стать со-организатором игры {game.name}?\n"
                    "В случае согласия будет невозможно сыграть в эту игру."
                )
            ),
            reply_markup=kb.get_kb_agree_be_org(token=token, inviter=player)
        )
    ]
    await q.answer(results=result, is_personal=True, cache_time=1)


async def dismiss_to_be_org_handler(c: CallbackQuery, callback_data: kb.AgreeBeOrgCD, dao: HolderDao, bot: Bot):
    await dismiss_to_be_org(callback_data.token, dao.secure_invite)
    await c.answer("правильно, лучше поиграть!", show_alert=True)
    await bot.edit_message_text(text="<i>(Игрок отказался от приглашения)</i>", inline_message_id=c.inline_message_id)


async def inviter_click_handler(c: CallbackQuery, callback_data: kb.AgreeBeOrgCD, dao: HolderDao):
    await c.answer("ну и смысл?", cache_time=30)


def setup() -> Router:
    router = Router(name=__name__)
    router.inline_query.register(invite_org_inline_query, kb.AddGameOrgID.filter())
    router.callback_query.register(
        inviter_click_handler, kb.AgreeBeOrgCD.filter(),
        MagicData(F.callback_data.inviter_id == F.player.id),
    )
    router.callback_query.register(dismiss_to_be_org_handler, kb.AgreeBeOrgCD.filter(~F.is_agreement))
    return router
