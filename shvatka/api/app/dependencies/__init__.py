from dishka import AsyncContainer, Provider, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from shvatka.api.app.dependencies.api_only import ApiOnlyProvider
from shvatka.api.app.dependencies.auth import AuthProvider
from shvatka.api.app.dependencies.config import ApiConfigProvider
from shvatka.api.app.dependencies.other import OtherApiProvider
from shvatka.infrastructure.di import get_providers
from shvatka.infrastructure.di.interactors import AdminProvider as AdminInteractorProvider
from shvatka.infrastructure.di.interactors import GameEditProvider


def setup_di(app: FastAPI, paths_env: str):
    container = create_dishka(paths_env)
    setup_dishka(container, app)
    # dishka's fastapi integration doesn't close the container itself, and
    # app-scoped things (the nursery among them) finalize on that close
    app.router.add_event_handler("shutdown", container.close)


def create_dishka(paths_env: str) -> AsyncContainer:
    return make_async_container(*get_api_providers(paths_env))


def get_api_providers(paths_env: str) -> list[Provider]:
    return [
        *get_providers(paths_env),
        *get_api_specific_providers(),
        *get_api_only_providers(),
    ]


def get_api_specific_providers() -> list[Provider]:
    return [
        AuthProvider(),
        AdminInteractorProvider(),
        ApiConfigProvider(),
        OtherApiProvider(),
        GameEditProvider(),
    ]


def get_api_only_providers() -> list[Provider]:
    return [
        ApiOnlyProvider(),
    ]
