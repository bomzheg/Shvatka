from dataclasses import dataclass

import dature

from shvatka.api.app.config.models.main import ApiConfig
from shvatka.api.app.config.parser.auth import load_auth
from shvatka.api.app.config.parser.push import load_push
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.config_source import config_source
from shvatka.common.config.parser.main import load_config as load_common_config


@dataclass(frozen=True, slots=True)
class ApiSection:
    """Keys of the api section which are not a section on their own."""

    context_path: str = ""
    enable_logging: bool = False


def load_config(paths: Paths) -> ApiConfig:
    api = load_api_section(paths)
    return ApiConfig.from_base(
        base=load_common_config(paths),
        auth=load_auth(paths),
        context_path=api.context_path,
        enable_logging=api.enable_logging,
        push=load_push(paths),
    )


def load_api_section(paths: Paths) -> ApiSection:
    return dature.load(config_source(paths, prefix="api"), schema=ApiSection)
