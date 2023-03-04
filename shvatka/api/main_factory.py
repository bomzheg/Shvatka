import logging

from fastapi import FastAPI

from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.paths import common_get_paths

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    return FastAPI()


def get_paths() -> Paths:
    return common_get_paths("API_PATH")
