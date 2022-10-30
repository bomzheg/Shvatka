import logging

import dataclass_factory
import uvicorn as uvicorn

from api import dependencies, routes
from api.config.parser.main import load_config
from api.main_factory import (
    get_paths,
    create_app,
)
from common.config.parser.logging_config import setup_logging
from db.fatory import create_pool, create_redis
from shvatka.models.schems import schemas

logger = logging.getLogger(__name__)


def main():
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    dcf = dataclass_factory.Factory(schemas=schemas)
    app = create_app()
    pool = create_pool(config.db)
    dependencies.setup(
        app=app,
        pool=pool,
        redis=create_redis(config.redis),
        config=config
    )
    routes.setup(app.router)

    logger.info("started")
    return app


if __name__ == '__main__':
    uvicorn.run(
        'api:main',
        factory=True,
        log_config=None
    )