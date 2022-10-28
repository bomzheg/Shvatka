import logging

import dataclass_factory
import uvicorn as uvicorn
from fastapi import Depends

from api.auth import User, Token, AuthProvider, get_current_user, get_current_active_user
from api.config.parser.logging_config import setup_logging
from api.config.parser.main import load_config
from api.main_factory import (
    get_paths,
    create_pool,
    create_app,
)
from shvatka.models.schems import schemas

logger = logging.getLogger(__name__)


async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]


async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


def main():
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    dcf = dataclass_factory.Factory(schemas=schemas)
    pool = create_pool(config.db)
    app = create_app()
    auth = AuthProvider()
    app.dependency_overrides[get_current_user] = auth.get_current_user
    app.dependency_overrides[get_current_active_user] = get_current_active_user

    app.router.add_api_route("/users/0", read_users_me, methods=["GET"], response_model=User)
    app.router.add_api_route("/users/0/items", read_own_items, methods=["GET"])
    app.router.add_api_route("/token", auth.login, methods=["POST"], response_model=Token)

    logger.info("started")
    return app


if __name__ == '__main__':
    uvicorn.run(
        'api:main',
        factory=True,
        log_config=None
    )
