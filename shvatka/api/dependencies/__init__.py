from dishka import Provider, make_async_container, AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from shvatka.api.dependencies.auth import AuthProvider, ApiIdpProvider
from shvatka.api.dependencies.config import ApiConfigProvider
from shvatka.infrastructure.di import get_providers


def setup_di(app: FastAPI, paths_env: str):
    container = create_dishka(paths_env)
    setup_dishka(container, app)


def create_dishka(paths_env: str) -> AsyncContainer:
    container = make_async_container(*get_api_providers(paths_env))
    return container


def get_api_providers(paths_env: str) -> list[Provider]:
    return [
        *get_providers(paths_env),
        *get_api_specific_providers(),
        *get_api_only_providers(),
    ]


def get_api_specific_providers() -> list[Provider]:
    return [
        AuthProvider(),
        ApiConfigProvider(),
    ]


def get_api_only_providers() -> list[Provider]:
    return [
        ApiIdpProvider(),
    ]
