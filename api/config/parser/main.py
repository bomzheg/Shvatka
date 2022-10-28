import yaml

from api.config.models.main import Paths, Config
from db.config.parser.db import load_db_config, load_redis_config
from db.config.parser.storage import load_storage_config


def load_config(paths: Paths) -> Config:
    with (paths.config_path / "config.yml").open("r") as f:
        config_dct = yaml.safe_load(f)

    return Config(
        paths=paths,
        db=load_db_config(config_dct["db"]),
        storage=load_storage_config(config_dct["storage"]),
        redis=load_redis_config(config_dct["redis"]),
    )
