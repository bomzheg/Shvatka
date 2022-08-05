import asyncio
from pathlib import Path

import pytest
from dataclass_factory import Factory

from app.config.logging_config import setup_logging
from app.config.main import load_config
from app.models.config.main import Paths, Config


@pytest.fixture(scope="session", autouse=True)
def app_config(paths: Paths) -> Config:
    setup_logging(paths)
    return load_config(paths)


@pytest.fixture(scope="session")
def paths():
    return Paths(Path(__file__).parent)


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
    return Factory()
