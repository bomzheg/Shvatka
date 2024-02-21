import logging

import uvicorn
from fastapi import FastAPI

from shvatka.api.main_factory import (
   create_app_with_dishka,
)
from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.common.config.parser.paths import common_get_paths

logger = logging.getLogger(__name__)


def main() -> FastAPI:
    paths = common_get_paths("SHVATKA_API_PATH")
    setup_logging(paths)

    app = create_app_with_dishka("SHVATKA_API_PATH")
    logger.info("app prepared")
    return app


def run():
    uvicorn.run("shvatka.api.__main__:main", factory=True, log_config=None)


if __name__ == "__main__":
    run()
