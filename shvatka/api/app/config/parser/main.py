from datetime import timedelta

import dature
from dature import F

from shvatka.api.app.config.models.main import ApiConfig
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.config_source import config_source


def load_config(paths: Paths) -> ApiConfig:
    return dature.load(
        config_source(
            paths,
            # the config states the token lifetime in minutes, the model keeps a timedelta
            field_mapping={F[ApiConfig].api.auth.token_expire: "token-expire-minutes"},
            type_loaders={timedelta: lambda minutes: timedelta(minutes=int(minutes))},
        ),
        schema=ApiConfig,
    )
