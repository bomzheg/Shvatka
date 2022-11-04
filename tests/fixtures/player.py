import pytest_asyncio

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.services.player import upsert_player
from shvatka.services.user import upsert_user
from tests.fixtures.user_constants import create_dto_hermione, create_dto_harry, create_dto_ron, create_dto_rowling


@pytest_asyncio.fixture
async def hermione(dao: HolderDao):
    return await create_hermi_player(dao)


@pytest_asyncio.fixture
async def harry(dao: HolderDao):
    return await create_harry_player(dao)


@pytest_asyncio.fixture
async def author(dao: HolderDao):
    return await create_author(dao)


@pytest_asyncio.fixture
async def ron(dao: HolderDao):
    return await create_ron_player(dao)


async def create_hermi_player(dao: HolderDao) -> dto.Player:
    return await upsert_player(await upsert_user(create_dto_hermione(), dao.user), dao.player)


async def create_harry_player(dao: HolderDao) -> dto.Player:
    return await upsert_player(await upsert_user(create_dto_harry(), dao.user), dao.player)


async def create_author(dao: HolderDao) -> dto.Player:
    author_ = await upsert_player(await upsert_user(create_dto_rowling(), dao.user), dao.player)
    await dao.player.promote(author_, author_)
    await dao.commit()
    author_.can_be_author = True
    return author_


async def create_ron_player(dao: HolderDao) -> dto.Player:
    return await upsert_player(await upsert_user(create_dto_ron(), dao.user), dao.player)
