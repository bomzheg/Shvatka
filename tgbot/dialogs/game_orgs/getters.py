from aiogram_dialog import DialogManager

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services import organizers
from shvatka.services.game import get_game
from tgbot.keyboards.inline import AddGameOrg


async def get_orgs(dialog_manager: DialogManager, **_):
    game_id = dialog_manager.start_data["game_id"]
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    author: dto.Player = dialog_manager.middleware_data["player"]
    game = await get_game(game_id, author, dao.game)
    orgs = await organizers.get_secondary_orgs(game, dao.organizer)
    inline_query = AddGameOrg(
        game_manage_token=game.manage_token,
        game_id=game.id,
        inviter_id=author.id,
    )
    return {
        "game": game,
        "orgs": orgs,
        "inline_query": inline_query.pack(),
    }
