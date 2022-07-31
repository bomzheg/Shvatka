"""
Test can find forgotten downgrade methods, undeleted data types in downgrade
methods, typos and many other errors.
Does not require any maintenance - you just add it once to check 80% of typos
and mistakes in migrations forever.
"""

import pytest
from alembic.command import downgrade, upgrade
from alembic.config import Config
from alembic.script import Script, ScriptDirectory

from app.models.config.main import Paths


def get_revisions():
    # Get directory object with Alembic migrations
    revisions_dir = ScriptDirectory("migrations")

    # Get & sort migrations, from first to last
    revisions = list(revisions_dir.walk_revisions('base', 'heads'))
    revisions.reverse()
    return revisions


@pytest.fixture()
def alembic_config(postgres_url: str, paths: Paths) -> Config:
    alembic_cfg = Config(str(paths.app_dir.parent / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(paths.app_dir.parent / "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", postgres_url)
    return alembic_cfg


@pytest.mark.first
@pytest.mark.parametrize('revision', get_revisions())
def test_migrations_stairway(revision: Script, alembic_config: Config):
    upgrade(alembic_config, revision.revision)

    # We need -1 for downgrading first migration (its down_revision is None)
    downgrade(alembic_config, revision.down_revision or '-1')
    upgrade(alembic_config, revision.revision)
