import asyncio
from pathlib import Path

import pytest

from src.common import Paths
from src.common import create_dataclass_factory
from src.common import setup_logging
from src.tgbot.config.models.main import TgBotConfig
from src.tgbot.config.parser.main import load_config


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
    return create_dataclass_factory()
