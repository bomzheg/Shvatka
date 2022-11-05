from fastapi import FastAPI
from redis.asyncio.client import Redis
from sqlalchemy.orm import sessionmaker

from api.config.models.main import ApiConfig
from api.dependencies.auth import get_current_user, AuthProvider
from api.dependencies.db import DbProvider, dao_provider
from api.dependencies.game import active_game_provider, db_game_provider
from api.dependencies.player import player_provider, db_player_provider
from api.dependencies.team import team_provider, db_team_provider


def setup(app: FastAPI, pool: sessionmaker, redis: Redis, config: ApiConfig):
    db_provider = DbProvider(pool=pool, redis=redis)

    auth_provider = AuthProvider(config.auth)
    app.include_router(auth_provider.router)

    app.dependency_overrides[get_current_user] = auth_provider.get_current_user
    app.dependency_overrides[dao_provider] = db_provider.dao
    app.dependency_overrides[AuthProvider] = lambda: auth_provider
    app.dependency_overrides[player_provider] = db_player_provider
    app.dependency_overrides[team_provider] = db_team_provider
    app.dependency_overrides[active_game_provider] = db_game_provider
