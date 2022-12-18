from infrastructure.db.config.models.db import DBConfig, RedisConfig


def load_db_config(db_dict: dict) -> DBConfig:
    return DBConfig(
        type=db_dict.get('type', None),
        connector=db_dict.get('connector', None),
        host=db_dict.get('host', None),
        port=db_dict.get('port', None),
        login=db_dict.get('login', None),
        password=db_dict.get('password', None),
        name=db_dict.get('name', None),
        path=db_dict.get('path', None),
        echo=db_dict.get("echo", False),
    )


def load_redis_config(redis_dict: dict) -> RedisConfig:
    return RedisConfig(
        url=redis_dict["url"],
        port=redis_dict.get("port", None),
        db=redis_dict.get("db", None),
    )
