from dataclasses import dataclass

from shvatka.infrastructure.db.config.models.db import DBConfig as TrueConfig


@dataclass
class DBConfig(TrueConfig):
    uri_: str
    echo: bool = False

    @property
    def uri(self) -> str:
        return self.uri_
