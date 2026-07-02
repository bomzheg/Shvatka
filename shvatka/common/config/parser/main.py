from dataclass_factory import Factory

from shvatka.common.config.models.main import (
    Config,
    FileStorageConfig,
    AppConfig,
    WebConfig,
    MailConfig,
)
from shvatka.common.config.models.paths import Paths
from shvatka.infrastructure.db.config.parser.db import load_db_config, load_redis_config


def load_config(config_dct: dict, paths: Paths, dcf: Factory) -> Config:
    return Config(
        paths=paths,
        db=load_db_config(config_dct["db"]),
        redis=load_redis_config(config_dct["redis"]),
        file_storage_config=load_file_storage_config(config_dct["file-storage-config"], dcf),
        app=load_app_config(config_dct["app"], dcf),
        web=load_web_config(config_dct["web"], dcf),
        mail=load_mail_config(config_dct.get("mail"), dcf),
    )


def load_mail_config(config_dct: dict | None, dcf: Factory) -> MailConfig:
    if not config_dct:
        return MailConfig()
    return MailConfig(
        enabled=bool(config_dct.get("enabled", False)),
        host=config_dct.get("host", ""),
        port=int(config_dct.get("port", 587)),
        username=config_dct.get("username", ""),
        password=config_dct.get("password", ""),
        from_addr=config_dct.get("from-addr", ""),
        use_tls=bool(config_dct.get("use-tls", False)),
        start_tls=bool(config_dct.get("start-tls", True)),
    )


def load_app_config(config_dct: dict, dcf: Factory) -> AppConfig:
    return dcf.load(config_dct, AppConfig)


def load_file_storage_config(config_dct: dict, dcf: Factory) -> FileStorageConfig:
    return dcf.load(config_dct, FileStorageConfig)


def load_web_config(config_dct: dict, dcf: Factory) -> WebConfig:
    return dcf.load(config_dct, WebConfig)
