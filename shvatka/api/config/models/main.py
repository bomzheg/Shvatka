from __future__ import annotations

from dataclasses import dataclass

from shvatka.api.config.models.auth import AuthConfig
from shvatka.common.config.models.main import Config


@dataclass
class ApiConfig(Config):
    auth: AuthConfig

    @classmethod
    def from_base(cls, base: Config, auth: AuthConfig):
        return cls(
            paths=base.paths,
            db=base.db,
            redis=base.redis,
            auth=auth,
            file_storage_config=base.file_storage_config,
        )
