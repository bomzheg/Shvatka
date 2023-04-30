import pytest_asyncio

from shvatka.core.models import dto
from shvatka.core.services.player import upsert_player
from shvatka.core.services.user import upsert_user
from shvatka.infrastructure.db.dao.holder import HolderDao
from tests.fixtures.user_constants import (
    create_dto_hermione,
    create_dto_harry,
    create_dto_ron,
    create_dto_rowling,
    create_dto_draco,
)


@pytest_asyncio.fixture
async def hermione(dao: HolderDao):
    return await create_player(create_dto_hermione(), dao)


@pytest_asyncio.fixture
async def harry(dao: HolderDao):
    player = await create_player(create_dto_harry(), dao)
    await promote(player, dao)
    return player


@pytest_asyncio.fixture
async def author(dao: HolderDao) -> dto.Player:
    author_ = await create_player(create_dto_rowling(), dao)
    await promote(author_, dao)
    return author_


@pytest_asyncio.fixture
async def ron(dao: HolderDao):
    return await create_player(create_dto_ron(), dao)


@pytest_asyncio.fixture
async def draco(dao: HolderDao):
    player = await create_player(create_dto_draco(), dao)
    await promote(player, dao)
    return player


async def create_player(user: dto.User, dao: HolderDao) -> dto.Player:
    return await upsert_player(await upsert_user(user, dao.user), dao.player)


async def promote(player: dto.Player, dao: HolderDao):
    await dao.player.promote(player, player)
    await dao.commit()
    player.can_be_author = True
