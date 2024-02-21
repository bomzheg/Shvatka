from dataclass_factory import Factory, Schema, NameStyle

from shvatka.infrastructure.db.config.models.db import DBConfig, RedisConfig, DBConfigProperties

dcf = Factory(default_schema=Schema(name_style=NameStyle.kebab))


def load_db_config(db_dict: dict) -> DBConfig:
    return dcf.load(db_dict, DBConfigProperties)


def load_redis_config(redis_dict: dict) -> RedisConfig:
    return dcf.load(redis_dict, RedisConfig)
