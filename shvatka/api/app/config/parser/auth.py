from datetime import timedelta

import dature
from dature import F

from shvatka.api.app.config.models.auth import AuthConfig
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.config_source import config_source


def load_auth(paths: Paths) -> AuthConfig:
    return dature.load(
        config_source(
            paths,
            prefix="api.auth",
            # the config states the lifetime in minutes, the model keeps a timedelta
            field_mapping={F[AuthConfig].token_expire: "token-expire-minutes"},
            type_loaders={timedelta: lambda minutes: timedelta(minutes=int(minutes))},
        ),
        schema=AuthConfig,
    )
