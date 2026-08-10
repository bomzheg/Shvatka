from typing import Callable

import pytest
from dishka import STRICT_VALIDATION, Provider, make_async_container

from shvatka.api.app.dependencies import get_api_providers
from shvatka.main_factory import get_root_app_providers
from shvatka.tgbot.main_factory import get_bot_providers
from tests.fixtures.di import get_test_providers


@pytest.mark.parametrize(
    "providers_factory",
    [
        pytest.param(lambda: get_api_providers("SHVATKA_PATH"), id="api"),
        pytest.param(lambda: get_bot_providers("SHVATKA_PATH"), id="bot"),
        pytest.param(lambda: get_root_app_providers("SHVATKA_PATH"), id="root"),
        pytest.param(get_test_providers, id="tests"),
    ],
)
def test_container_can_be_built(providers_factory: Callable[[], list[Provider]]):
    """Every dependency is resolvable and every test double really overrides one."""
    make_async_container(*providers_factory(), validation_settings=STRICT_VALIDATION)
