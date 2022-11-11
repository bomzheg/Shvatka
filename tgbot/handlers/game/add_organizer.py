from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.game import get_game
from shvatka.services.organizers import check_allow_add_orgs
from tgbot import keyboards as kb


async def add_org_inline_query(q: InlineQuery, inline_data: kb.AddGameOrg, player: dto.Player, dao: HolderDao):
    game = await get_game(id_=inline_data.game_id, dao=dao.game)
    await check_allow_add_orgs(game, inline_data.game_manage_token, player)
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
            # reply_markup=kb.get_agree_be_org(salt)  # TODO
        )
    ]
    await q.answer(results=result, is_personal=True, cache_time=1)


def setup() -> Router:
    router = Router(name=__name__)
    router.inline_query.register(add_org_inline_query, kb.AddGameOrg.filter())
    return router
