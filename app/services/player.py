from app.dao import PlayerDao, PlayerInTeamDao
from app.models import dto
from app.utils.defaults_constants import DEFAULT_ROLE


async def upsert_player(user: dto.User, dao: PlayerDao) -> dto.Player:
    player_user = await dao.upsert_player(user)
    await dao.commit()
    return player_user


async def have_team(player: dto.Player, dao: PlayerInTeamDao) -> bool:
    return await dao.have_team(player)


async def get_my_team(player: dto.Player, dao: PlayerInTeamDao) -> dto.Team:
    return await dao.get_team(player)


async def add_player_in_team(
    player: dto.Player, team: dto.Team,
    dao: PlayerInTeamDao, role: str = DEFAULT_ROLE,
):
    await dao.add_in_team(player, team, role=role)
    await dao.commit()
