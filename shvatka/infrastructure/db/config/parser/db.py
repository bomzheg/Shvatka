from adaptix import Retort, NameStyle, name_mapping

from shvatka.infrastructure.db.config.models.db import DBConfig, RedisConfig, DBConfigProperties

dcf = Retort(recipe=[name_mapping(name_style=NameStyle.LOWER_KEBAB)])


def load_db_config(db_dict: dict) -> DBConfig:
    return dcf.load(db_dict, DBConfigProperties)


def load_redis_config(redis_dict: dict) -> RedisConfig:
    return dcf.load(redis_dict, RedisConfig)
