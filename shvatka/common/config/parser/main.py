from dataclasses import dataclass, field

import dature

from shvatka.common.config.models.main import (
    Config,
    FileStorageConfig,
    AppConfig,
    WebConfig,
    MailConfig,
)
from shvatka.common.config.models.paths import Paths
from shvatka.common.config.parser.config_source import config_source
from shvatka.infrastructure.db.config.parser.db import load_db_config, load_redis_config


@dataclass(frozen=True, slots=True)
class SharedSection:
    """Top level keys of config.yml which don't belong to any named section."""

    superusers: list[int] = field(default_factory=list)


def load_config(paths: Paths) -> Config:
    return Config(
        paths=paths,
        db=load_db_config(paths),
        redis=load_redis_config(paths),
        file_storage_config=load_file_storage_config(paths),
        app=load_app_config(paths),
        web=load_web_config(paths),
        mail=load_mail_config(paths),
        superusers=load_shared_section(paths).superusers,
    )


def load_shared_section(paths: Paths) -> SharedSection:
    return dature.load(config_source(paths), schema=SharedSection)


def load_mail_config(paths: Paths) -> MailConfig:
    return dature.load(config_source(paths, prefix="mail"), schema=MailConfig)


def load_app_config(paths: Paths) -> AppConfig:
    return dature.load(config_source(paths, prefix="app"), schema=AppConfig)


def load_file_storage_config(paths: Paths) -> FileStorageConfig:
    return dature.load(
        config_source(paths, prefix="file-storage-config"), schema=FileStorageConfig
    )


def load_web_config(paths: Paths) -> WebConfig:
    return dature.load(config_source(paths, prefix="web"), schema=WebConfig)
