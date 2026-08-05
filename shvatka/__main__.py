"""Entrypoint of the combined (api + tgbot webhook) application.

This module is deliberately kept free of heavy imports: it must be able to
configure logging before anything else is loaded, otherwise the whole import
of the application (aiogram, pyrogram, matplotlib, sqlalchemy, ...) happens in
complete silence and the process looks hung for tens of seconds.
"""

import uvicorn
import logging
import time
from typing import TYPE_CHECKING

from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.common.config.parser.paths import common_get_paths

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


def main() -> "FastAPI":
    paths = common_get_paths("API_PATH")
    setup_logging(paths)
    logger.info("logging configured, loading application modules...")
    started_at = time.monotonic()
    from shvatka.main_factory import create_root_app

    logger.info("application modules loaded in %.2f s", time.monotonic() - started_at)
    return create_root_app(paths)


def run():
    uvicorn.run(
        "shvatka.__main__:main",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        factory=True,
        log_config=None,
    )


if __name__ == "__main__":
    run()
