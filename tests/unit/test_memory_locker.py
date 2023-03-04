import pytest

from shvatka.core.models import dto
from shvatka.infrastructure.db.dao.memory.locker import MemoryLockFactory


@pytest.mark.asyncio
async def test_same_lock():
    locker = MemoryLockFactory()
    team_1 = dto.Team(1, *[None] * 5)
    team_2 = dto.Team(1, *[None] * 5)

    lock1 = locker(team_1)
    lock2 = locker(team_2)
    assert lock1 is lock2


@pytest.mark.asyncio
async def test_other_lock():
    locker = MemoryLockFactory()
    team_1 = dto.Team(1, *[None] * 5)
    team_2 = dto.Team(2, *[None] * 5)

    lock1 = locker(team_1)
    lock2 = locker(team_2)
    assert lock1 is not lock2
