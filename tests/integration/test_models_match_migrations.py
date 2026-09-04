import pytest
from dishka import AsyncContainer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from shvatka.infrastructure.db.models import Base

# Indexes backing a primary key or unique constraint are owned by that
# constraint, not declared as Index() on the model, so they are not compared.
STANDALONE_INDEXES = text(
    """
    SELECT i.indexname
    FROM pg_indexes i
    JOIN pg_class c ON c.relname = i.indexname
    LEFT JOIN pg_constraint con ON con.conindid = c.oid
    WHERE i.schemaname = current_schema()
      AND con.oid IS NULL
"""
)


@pytest.mark.asyncio
async def test_indexes_match_models(dishka: AsyncContainer) -> None:
    engine = await dishka.get(AsyncEngine)
    async with engine.connect() as connection:
        result = await connection.execute(STANDALONE_INDEXES)
        in_db = {row[0] for row in result}

    on_models = {
        str(index.name)
        for table in Base.metadata.sorted_tables
        for index in table.indexes
        if index.name is not None
    }

    assert not (in_db - on_models), (
        "indexes exist in the database but are not declared on any model: "
        f"{sorted(in_db - on_models)}"
    )
    assert not (on_models - in_db), (
        "indexes are declared on models but no migration creates them: "
        f"{sorted(on_models - in_db)}"
    )
