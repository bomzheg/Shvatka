from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.chat import upsert_chat
from shvatka.services.team import create_team
from tests.fixtures.chat_constants import create_dto_chat, create_another_chat


async def create_first_team(captain: dto.Player, dao: HolderDao) -> dto.Team:
    return await create_team(
        await upsert_chat(create_dto_chat(), dao.chat), captain, dao.team_creator,
    )


async def create_second_team(captain: dto.Player, dao: HolderDao) -> dto.Team:
    return await create_team(
        await upsert_chat(create_another_chat(), dao.chat), captain, dao.team_creator,
    )
