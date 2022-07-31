from app.dao import TeamDao
from app.models import dto


async def create_team(chat: dto.Chat, captain: dto.Player, dao: TeamDao) -> dto.Team:
    team = await dao.create(chat, captain)
    await dao.commit()
    return team


async def get_by_chat(chat: dto.Chat, dao: TeamDao) -> dto.Team | None:
    return await dao.get_by_chat(chat)
