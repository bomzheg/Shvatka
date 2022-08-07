from app.dao.holder import HolderDao
from app.models import dto
from app.services.chat import upsert_chat
from app.services.team import create_team
from tests.fixtures.chat_constants import create_dto_chat, create_another_chat


async def create_first_team(captain: dto.Player, dao: HolderDao) -> dto.Team:
    return await create_team(await upsert_chat(create_dto_chat(), dao.chat), captain, dao)


async def create_second_team(captain: dto.Player, dao: HolderDao) -> dto.Team:
    return await create_team(await upsert_chat(create_another_chat(), dao.chat), captain, dao)
