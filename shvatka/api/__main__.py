import logging

import uvicorn
from fastapi import FastAPI

from shvatka.api.config.parser.main import load_config
from shvatka.api.dependencies import setup_di
from shvatka.api.main_factory import (
    create_app,
)
from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.common.config.parser.paths import common_get_paths

logger = logging.getLogger(__name__)


def main() -> FastAPI:
    paths = common_get_paths("SHVATKA_API_PATH")
    setup_logging(paths)
    api_config = load_config(paths)

    app = create_app(api_config)
    root_app = FastAPI()
    root_app.mount(api_config.context_path, app)
    setup_di(root_app, "SHVATKA_API_PATH")
    logger.info("app prepared")
    return root_app


def run():
    uvicorn.run("shvatka.api.__main__:main", factory=True, log_config=None)


if __name__ == "__main__":
    run()
