from dataclass_factory import Factory, Schema, NameStyle

from shvatka.api.config.models.main import ApiConfig
from shvatka.api.config.parser.auth import load_auth
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.config_file_reader import read_config
from shvatka.common.config.parser.main import load_config as load_common_config


def load_config(paths: Paths) -> ApiConfig:
    dcf = Factory(default_schema=Schema(name_style=NameStyle.kebab))
    config_dct = read_config(paths)
    return ApiConfig.from_base(
        base=load_common_config(config_dct, paths, dcf),
        auth=load_auth(config_dct["auth"]),
        context_path=config_dct.get("context-path", ""),
    )
