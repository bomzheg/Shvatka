import dature

from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.config_source import config_source
from shvatka.infrastructure.db.config.models.db import DBConfig, RedisConfig, DBConfigProperties


def load_db_config(paths: Paths) -> DBConfig:
    return dature.load(config_source(paths, prefix="db"), schema=DBConfigProperties)


def load_redis_config(paths: Paths) -> RedisConfig:
    return dature.load(config_source(paths, prefix="redis"), schema=RedisConfig)
