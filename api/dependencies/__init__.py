from fastapi import FastAPI
from redis.asyncio.client import Redis
from sqlalchemy.orm import sessionmaker

from api.config.models.main import ApiConfig
from api.dependencies.auth import get_current_user, AuthProvider, Token
from api.dependencies.db import DbProvider, dao_provider


def setup(app: FastAPI, pool: sessionmaker, redis: Redis, config: ApiConfig):
    db_provider = DbProvider(pool=pool, redis=redis)

    auth_provider = AuthProvider(config.auth)
    app.include_router(auth_provider.setup_auth_routes())

    app.dependency_overrides[get_current_user] = auth_provider.get_current_user
    app.dependency_overrides[dao_provider] = db_provider.dao
    app.dependency_overrides[AuthProvider] = lambda: auth_provider
