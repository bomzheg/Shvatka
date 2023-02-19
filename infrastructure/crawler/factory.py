from common.config.models.paths import Paths
from common.config.parser.paths import common_get_paths


def get_paths() -> Paths:
    return common_get_paths("CRAWLER_PATH")
