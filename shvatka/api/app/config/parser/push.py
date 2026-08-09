import dature

from shvatka.api.app.config.models.push import PushConfig
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.config_source import config_source


def load_push(paths: Paths) -> PushConfig:
    return dature.load(config_source(paths, prefix="api.push"), schema=PushConfig)
