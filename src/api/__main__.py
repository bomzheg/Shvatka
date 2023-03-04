import logging

import dataclass_factory
import uvicorn as uvicorn
from dataclass_factory import Schema, NameStyle
from fastapi import FastAPI

from src.api import dependencies, routes
from src.api.config.parser.main import load_config
from src.api.main_factory import (
    get_paths,
    create_app,
)
from src.common.config.parser.logging_config import setup_logging
from src.infrastructure.db.faсtory import create_pool, create_redis
from src.shvatka.models.schems import schemas

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


if __name__ == "__main__":
    uvicorn.run("src.api:main", factory=True, log_config=None)
