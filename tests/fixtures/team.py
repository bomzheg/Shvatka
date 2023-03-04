import pytest_asyncio

from src.infrastructure.db.dao.holder import HolderDao
from src.core.models import dto
from src.core.services.chat import upsert_chat
from src.core.services.team import create_team
from tests.fixtures.chat_constants import create_gryffindor_dto_chat, create_slytherin_dto_chat


@pytest_asyncio.fixture
async def gryffindor(harry: dto.Player, dao: HolderDao):
    return await create_team_(harry, create_gryffindor_dto_chat(), dao)


@pytest_asyncio.fixture
async def slytherin(draco: dto.Player, dao: HolderDao):
    return await create_team_(draco, create_slytherin_dto_chat(), dao)


async def create_team_(captain: dto.Player, chat: dto.Chat, dao: HolderDao) -> dto.Team:
    return await create_team(
        await upsert_chat(chat, dao.chat),
        captain,
        dao.team_creator,
    )


async def create_second_team(captain: dto.Player, dao: HolderDao) -> dto.Team:
    return await create_team(
        await upsert_chat(create_slytherin_dto_chat(), dao.chat),
        captain,
        dao.team_creator,
    )
