"""Every app's dependency graph must be complete before it starts.

A use case that lives in the shared providers is wired differently in each
app — a bot view here, a web one there — and it is easy to bind it in one
container and forget another. Dishka checks the whole graph when the container
is built, so building it is the test.
"""

import pytest
from dishka import STRICT_VALIDATION, Provider, make_async_container

from shvatka.api.app.dependencies import get_api_specific_providers
from shvatka.infrastructure.di import get_providers
from shvatka.main_factory import get_complex_only_providers
from shvatka.tgbot.main_factory import get_bot_only_providers, get_bot_specific_providers

PATHS_ENV = "SHVATKA_PATH"


def bot_providers() -> list[Provider]:
    return [*get_providers(PATHS_ENV), *get_bot_specific_providers(), *get_bot_only_providers()]


def complex_providers() -> list[Provider]:
    return [
        *get_providers(PATHS_ENV),
        *get_bot_specific_providers(),
        *get_api_specific_providers(),
        *get_complex_only_providers(),
    ]


@pytest.mark.parametrize(
    "providers",
    [
        pytest.param(bot_providers, id="bot"),
        pytest.param(complex_providers, id="complex"),
    ],
)
def test_container_graph_is_complete(providers):
    """No missing factory anywhere in the app's graph.

    Nothing is resolved here, so no config or database is needed — the
    container is built and thrown away.

    The api-only app is left out: it cannot provide `Retort`, which only the
    bot-specific `DCFProvider` offers, so its graph does not validate yet.
    """
    make_async_container(*providers(), validation_settings=STRICT_VALIDATION)
