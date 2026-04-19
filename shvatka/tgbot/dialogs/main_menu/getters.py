from aiogram_dialog import DialogManager
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from shvatka.core.games.interactors import GamePlayRoleReader
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.models import dto
from shvatka.core.services.player import save_promotion_invite
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import keyboards as kb
from shvatka.tgbot.services.identity import TgBotIdentityProvider


@inject
async def get_main(
    current_game: FromDishka[CurrentGameProvider],
    identity: FromDishka[TgBotIdentityProvider],
    interactor: FromDishka[GamePlayRoleReader],
    **_,
):
    game = await current_game.get_game()
    player = await identity.get_required_player()
    team = await identity.get_team()
    team_player = await identity.get_full_team_player()
    if game:
        my_role = await interactor(identity)
        org = my_role.org
        waiver = my_role.waiver_vote
    else:
        org = None
        waiver = None

    return {
        "player": player,
        "game": game,
        "org": org,
        "team": team,
        "team_player": team_player,
        "waiver": waiver,
    }


async def get_promotion_token(dialog_manager: DialogManager, **_):
    dao: HolderDao = dialog_manager.middleware_data["dao"]
    player: dto.Player = dialog_manager.middleware_data["player"]
    token = await save_promotion_invite(player, dao.secure_invite)
    return {
        "player": player,
        "inline_query": kb.PromotePlayerID(token=token).pack(),
    }
