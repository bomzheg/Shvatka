from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import get_team_player, get_my_team


async def get_my_team_(dao: HolderDao, player: dto.Player, **_) -> dict[str, dto.Team]:
    team = await get_my_team(player=player, dao=dao.team_player)
    team_player = await get_team_player(player=player, team=team, dao=dao.team_player)
    return {"team": team, "team_player": team_player}
