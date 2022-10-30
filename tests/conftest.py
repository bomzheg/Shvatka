import asyncio
from pathlib import Path

import pytest
from dataclass_factory import Factory

from common.config.models.paths import Paths
from common.config.parser.logging_config import setup_logging
from shvatka.models.schems import schemas
from tgbot.config.models.main import TgBotConfig
from tgbot.config.parser.main import load_config


@pytest.fixture(scope="session", autouse=True)
def bot_config(paths: Paths) -> TgBotConfig:
    return load_config(paths)


@pytest.fixture(scope="session")
def paths():
    paths = Paths(Path(__file__).parent)
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


@pytest.fixture(scope="session")
def dcf():
    return Factory(schemas=schemas)
