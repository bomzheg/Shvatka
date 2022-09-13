import asyncio
from pathlib import Path

import pytest
from dataclass_factory import Factory

from shvatka.config.logging_config import setup_logging
from shvatka.config.main import load_config
from shvatka.models.config.main import Paths, Config
from shvatka.models.schems import schemas


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
    return Factory(schemas=schemas)
