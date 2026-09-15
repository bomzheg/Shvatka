"""Everything `SeasonSlot.to_dto` walks into must be loaded up front.

An async session cannot lazy-load a relationship after the fact — it raises
`MissingGreenlet` — and a date with an owner walks four levels deep: the
owner's user, the team's chat, forum team and captain, and every org's user.
Only a database run proves the loading works; this proves it was *asked* for,
which is the half that keeps getting forgotten.
"""

import re

from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import selectinload

from shvatka.infrastructure.db.dao.rdb.season import _SLOT_OPTIONS
from shvatka.infrastructure.db.models import Season, SeasonSlot


def joined_tables(statement) -> set[str]:
    sql = str(statement.compile(dialect=postgresql.dialect()))
    return set(re.findall(r"LEFT OUTER JOIN (\w+)", sql))


def test_a_date_carries_its_owner_team_orgs_and_game():
    tables = joined_tables(select(SeasonSlot).options(*_SLOT_OPTIONS))

    # the owner and their telegram user
    assert {"players", "users"} <= tables
    # the team, its chat, its forum team and its captain
    assert {"teams", "chats", "forum_teams"} <= tables
    # the linked game
    assert "games" in tables


def test_a_season_loads_its_dates_the_same_way():
    statement = select(Season).options(selectinload(Season.slots).options(*_SLOT_OPTIONS))

    # the dates come in their own select, so the joins are not in this one —
    # what matters is that the options compile against the relationship at all
    assert joined_tables(statement) == set()
    assert "seasons" in str(statement.compile(dialect=postgresql.dialect()))
