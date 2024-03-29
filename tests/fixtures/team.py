import pytest_asyncio

from shvatka.core.models import dto
from shvatka.core.services.chat import upsert_chat
from shvatka.core.services.team import create_team
from shvatka.core.views.game import GameLogWriter
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.chat_constants import create_gryffindor_dto_chat, create_slytherin_dto_chat


@pytest_asyncio.fixture
async def gryffindor(harry: dto.Player, dao: HolderDao, game_log: GameLogWriter):
    return await create_team_(harry, create_gryffindor_dto_chat(), dao, game_log)


@pytest_asyncio.fixture
async def slytherin(draco: dto.Player, dao: HolderDao, game_log: GameLogWriter):
    return await create_team_(draco, create_slytherin_dto_chat(), dao, game_log)


async def create_team_(
    captain: dto.Player, chat: dto.Chat, dao: HolderDao, game_log: GameLogWriter
) -> dto.Team:
    return await create_team(
        await upsert_chat(chat, dao.chat),
        captain,
        dao.team_creator,
        game_log,
    )


async def create_second_team(
    captain: dto.Player, dao: HolderDao, game_log: GameLogWriter
) -> dto.Team:
    return await create_team(
        await upsert_chat(create_slytherin_dto_chat(), dao.chat),
        captain,
        dao.team_creator,
        game_log,
    )
