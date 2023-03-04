from src.common.config.models.paths import Paths
from src.common.config.parser.paths import common_get_paths


def get_paths() -> Paths:
    return common_get_paths("CRAWLER_PATH")
