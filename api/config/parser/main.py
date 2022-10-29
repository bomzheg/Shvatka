
from api.config.models.main import ApiConfig
from api.config.parser.auth import load_auth
from common.config.models.paths import Paths
from common.config.parser.config_file_reader import read_config
from common.config.parser.main import load_config as load_common_config


def load_config(paths: Paths) -> ApiConfig:
    config_dct = read_config(paths)
    return ApiConfig.from_base(
        base=load_common_config(config_dct, paths),
        auth=load_auth(config_dct["auth"]),
    )
