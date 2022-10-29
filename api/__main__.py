import logging

import dataclass_factory
import uvicorn as uvicorn
from fastapi import Depends

from api import dependencies
from api.config.parser.logging_config import setup_logging
from api.config.parser.main import load_config
from api.dependencies.auth import get_current_user
from api.main_factory import (
    get_paths,
    create_app,
)
from db.fatory import create_pool, create_redis
from shvatka.models import dto
from shvatka.models.schems import schemas

logger = logging.getLogger(__name__)


async def read_own_items(current_user: dto.User = Depends(get_current_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]


async def read_users_me(current_user: dto.User = Depends(get_current_user)):
    return current_user


def main():
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    dcf = dataclass_factory.Factory(schemas=schemas)
    app = create_app()
    pool = create_pool(config.db)
    dependencies.setup(app=app, pool=pool, redis=create_redis(config.redis))

    app.router.add_api_route("/users/0", read_users_me, methods=["GET"], response_model=dto.User)
    app.router.add_api_route("/users/0/items", read_own_items, methods=["GET"])

    logger.info("started")
    return app


if __name__ == '__main__':
    uvicorn.run(
        'api:main',
        factory=True,
        log_config=None
    )
