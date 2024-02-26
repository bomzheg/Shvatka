import logging
import sys

from shvatka.api.config.parser.main import load_config
from shvatka.api.main_factory import (
    get_paths,
)
from shvatka.common.config.parser.logging_config import setup_logging
from shvatka.api.dependencies.auth import AuthProperties

logger = logging.getLogger(__name__)


def generate():
    paths = get_paths()

    setup_logging(paths)
    config = load_config(paths)
    auth = AuthProperties(config.auth)
    return auth.get_password_hash(sys.argv[1])


if __name__ == "__main__":
    print(generate())  # noqa: T201
