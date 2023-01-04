import logging.config

import yaml
from sqlalchemy import log as sa_log

from common.config.models.paths import Paths

logger = logging.getLogger(__name__)


def setup_logging(paths: Paths):
    # manky patching logging sqlalchemy
    sa_log._add_default_handler = lambda _: None  # noqa
    try:
        with paths.logging_config_file.open("r") as f:
            logging_config = yaml.safe_load(f)
        logging.config.dictConfig(logging_config)
        logger.info("Logging configured successfully")
    except IOError:
        logging.basicConfig(level=logging.DEBUG)
        logger.warning("logging config file not found, use basic config")
