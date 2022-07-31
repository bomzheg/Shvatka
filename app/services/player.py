from app.dao import PlayerDao
from app.models import dto


async def upsert_player(user: dto.User, dao: PlayerDao) -> dto.Player:
    player_user = await dao.upsert_player(user)
    await dao.commit()
    return player_user
