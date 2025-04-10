import asyncio
import os
from pathlib import Path

import pytest
import pytest_asyncio
from adaptix import Retort
from dataclass_factory import Factory
from dishka import make_async_container

from shvatka.common import Paths
from shvatka.common import setup_logging
from shvatka.common.factory import DCFProvider
from shvatka.tgbot.config.models.main import TgBotConfig
from shvatka.tgbot.config.parser.main import load_config
from tests.fixtures.conftest import fixtures_resource_path  # noqa: F401
from tests.fixtures.player import harry, hermione, ron, author, draco  # noqa: F401
from tests.fixtures.scn_fixtures import simple_scn, complex_scn, three_lvl_scn, routed_scn
from tests.fixtures.team import gryffindor, slytherin  # noqa: F401
from tests.fixtures.game_fixtures import (  # noqa: F401
    game,
    finished_game,
    started_game,
    game_with_waivers,
    routed_game,
    routed_game_with_waivers,
    started_routed_game,
)
from tests.fixtures.scn_fixtures import simple_scn, complex_scn, three_lvl_scn, routed_scn  # noqa: F401
from tests.fixtures.game_results import game_stat  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def bot_config(paths: Paths) -> TgBotConfig:
    return load_config(paths)


@pytest.fixture(scope="session")
def paths():
    paths = Paths(Path(__file__).parent)
    os.environ["SHVATKA_TEST_PATH"] = str(paths.app_dir)
    setup_logging(paths)
    return paths


@pytest.fixture(scope="session")
def event_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


@pytest_asyncio.fixture(scope="session")
async def dcf():
    dishka = make_async_container(DCFProvider())
    return await dishka.get(Factory)


@pytest_asyncio.fixture(scope="session")
async def retort() -> Retort:
    dishka = make_async_container(DCFProvider())
    return await dishka.get(Retort)
