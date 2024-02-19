import logging

import uvicorn
from dishka.integrations.fastapi import DishkaApp

from shvatka.api.dependencies import setup_dishka
from shvatka.api.main_factory import (
    create_app,
)
from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.common.config.parser.paths import common_get_paths

logger = logging.getLogger(__name__)


def main() -> DishkaApp:
    paths = common_get_paths("SHVATKA_API_PATH")
    setup_logging(paths)

    app = create_app()
    dishka_app = setup_dishka(app, "SHVATKA_API_PATH")
    logger.info("app prepared")
    return dishka_app


def run():
    uvicorn.run("shvatka.api:main", factory=True, log_config=None)


if __name__ == "__main__":
    run()
