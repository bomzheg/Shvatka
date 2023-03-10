import logging

import dataclass_factory
import uvicorn as uvicorn
from dataclass_factory import Schema, NameStyle
from fastapi import FastAPI

from shvatka.api import dependencies, routes
from shvatka.api.config.parser.main import load_config
from shvatka.api.main_factory import (
    get_paths,
    create_app,
)
from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.core.models.schems import schemas
from shvatka.infrastructure.db.faсtory import create_pool, create_redis

logger = logging.getLogger(__name__)


def main() -> FastAPI:
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    dcf = dataclass_factory.Factory(
        schemas=schemas, default_schema=Schema(name_style=NameStyle.kebab)
    )
    app = create_app()
    pool = create_pool(config.db)
    dependencies.setup(app=app, pool=pool, redis=create_redis(config.redis), config=config)
    routes.setup(app.router)

    logger.info("app prepared")
    return app


def run():
    uvicorn.run("shvatka.api:main", factory=True, log_config=None)


if __name__ == "__main__":
    run()