from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import upsert_player
from shvatka.services.user import upsert_user
from tests.fixtures.user_constants import create_dto_hermione, create_dto_harry, create_dto_ron


async def create_hermi_player(dao: HolderDao) -> dto.Player:
    return await upsert_player(await upsert_user(create_dto_hermione(), dao.user), dao.player)


async def create_harry_player(dao: HolderDao) -> dto.Player:
    return await upsert_player(await upsert_user(create_dto_harry(), dao.user), dao.player)


async def create_ron_player(dao: HolderDao) -> dto.Player:
    return await upsert_player(await upsert_user(create_dto_ron(), dao.user), dao.player)
