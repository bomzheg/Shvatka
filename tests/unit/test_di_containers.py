import pytest
from dishka import STRICT_VALIDATION, Provider, make_async_container

from shvatka.api.app.dependencies import get_api_only_providers, get_api_specific_providers
from shvatka.infrastructure.di import get_providers
from shvatka.main_factory import get_root_app_providers
from shvatka.tgbot.main_factory import get_bot_only_providers, get_bot_specific_providers

PATHS_ENV = "SHVATKA_PATH"


def bot_providers() -> list[Provider]:
    return [*get_providers(PATHS_ENV), *get_bot_specific_providers(), *get_bot_only_providers()]


def api_providers() -> list[Provider]:
    return [*get_providers(PATHS_ENV), *get_api_specific_providers(), *get_api_only_providers()]


@pytest.mark.parametrize(
    "providers",
    [
        pytest.param(bot_providers, id="bot"),
        pytest.param(api_providers, id="api"),
        pytest.param(lambda: get_root_app_providers(PATHS_ENV), id="root"),
    ],
)
def test_container_graph_is_complete(providers):
    make_async_container(*providers(), validation_settings=STRICT_VALIDATION)
