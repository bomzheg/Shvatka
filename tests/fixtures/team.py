import pytest_asyncio

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.chat import upsert_chat
from shvatka.services.team import create_team
from tests.fixtures.chat_constants import create_dto_chat, create_another_chat


@pytest_asyncio.fixture
async def gryffindor(harry: dto.Player, dao: HolderDao):
    return await create_first_team(harry, create_dto_chat(), dao)


async def create_first_team(captain: dto.Player, chat: dto.Chat, dao: HolderDao) -> dto.Team:
    return await create_team(
        await upsert_chat(chat, dao.chat), captain, dao.team_creator,
    )


async def create_second_team(captain: dto.Player, dao: HolderDao) -> dto.Team:
    return await create_team(
        await upsert_chat(create_another_chat(), dao.chat), captain, dao.team_creator,
    )
