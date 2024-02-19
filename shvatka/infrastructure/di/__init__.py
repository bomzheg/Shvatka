from dishka.integrations.fastapi import DishkaApp
from fastapi import FastAPI

from shvatka.infrastructure.di.auth import AuthProvider
from shvatka.infrastructure.di.config import ConfigProvider
from shvatka.infrastructure.di.db import DbProviderD, RedisProvider
from shvatka.infrastructure.di.game import GameProvider
from shvatka.infrastructure.di.player import PlayerProvider
from shvatka.infrastructure.di.team import TeamProvider
from shvatka.api.utils.cookie_auth import OAuth2PasswordBearerWithCookie


def get_providers(paths_env):
    return [
        ConfigProvider(paths_env),
        DbProviderD(),
        RedisProvider(),
        AuthProvider(),
        OAuth2PasswordBearerWithCookie(token_url="auth/token"),
        GameProvider(),
        PlayerProvider(),
        TeamProvider(),
    ]
