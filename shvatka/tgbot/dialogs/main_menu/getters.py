from aiogram_dialog import DialogManager

from shvatka.core.models import dto
from shvatka.core.services.organizers import get_by_player_or_none
from shvatka.core.services.player import save_promotion_invite, get_my_team, get_full_team_player
from shvatka.core.services.waiver import get_my_waiver
from shvatka.core.utils.exceptions import PlayerNotInTeam
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import keyboards as kb


async def get_main(dao: HolderDao, player: dto.Player, game: dto.Game, **_):
    if game:
        org = await get_by_player_or_none(player=player, game=game, dao=dao.organizer)
    else:
        org = None
    try:
        team = await get_my_team(player=player, dao=dao.team_player)
        team_player = await get_full_team_player(player=player, team=team, dao=dao.team_player)
        if game and team:
            waiver = await get_my_waiver(player=player, team=team, game=game, dao=dao.waiver)
        else:
            waiver = None
    except PlayerNotInTeam:
        team = None
        team_player = None
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
