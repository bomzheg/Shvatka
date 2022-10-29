from fastapi import FastAPI
from redis.asyncio.client import Redis
from sqlalchemy.orm import sessionmaker

from api.dependencies.auth import get_current_user, AuthProvider, Token
from api.dependencies.db import DbProvider, dao_provider


def setup(app: FastAPI, pool: sessionmaker, redis: Redis):
    db_provider = DbProvider(pool=pool, redis=redis)
    auth_provider = AuthProvider()

    app.dependency_overrides[get_current_user] = auth_provider.get_current_user
    app.dependency_overrides[dao_provider] = db_provider.dao
    app.router.add_api_route("/token", auth_provider.login, methods=["POST"], response_model=Token)
