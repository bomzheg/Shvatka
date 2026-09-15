"""Locking a date that somebody else is editing fails instead of queueing.

`FOR UPDATE NOWAIT` is the whole mechanism, and postgres reports the refusal as
sqlstate 55P03. The dao turns that into `SlotIsBusy`; anything else is still a
database error and must travel on untouched. Waiting instead would mean reading
the date as it was before the other edit and then writing over it, which is the
one outcome the lock exists to prevent.
"""

import pytest
from sqlalchemy.exc import DBAPIError

from shvatka.core.utils import exceptions
from shvatka.infrastructure.db.dao.rdb.season_slot import LOCK_NOT_AVAILABLE, SeasonSlotDao

SERIALIZATION_FAILURE = "40001"
"""A different problem with a different fix: the caller must see it as itself."""


class FakeOrig(Exception):
    def __init__(self, sqlstate: str) -> None:
        super().__init__(sqlstate)
        self.sqlstate = sqlstate


class RefusingSession:
    """A session whose every execute fails the way a held row lock does."""

    def __init__(self, sqlstate: str) -> None:
        self.sqlstate = sqlstate

    async def execute(self, *args: object, **kwargs: object) -> None:
        raise DBAPIError("select ...", {}, FakeOrig(self.sqlstate))


def dao_refusing_with(sqlstate: str) -> SeasonSlotDao:
    return SeasonSlotDao(session=RefusingSession(sqlstate))


@pytest.mark.asyncio
async def test_a_date_somebody_else_is_editing_is_busy():
    with pytest.raises(exceptions.SlotIsBusy):
        await dao_refusing_with(LOCK_NOT_AVAILABLE).lock_slot(1)


@pytest.mark.asyncio
async def test_any_other_database_error_is_not_swallowed():
    with pytest.raises(DBAPIError):
        await dao_refusing_with(SERIALIZATION_FAILURE).lock_slot(1)
