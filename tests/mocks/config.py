from dataclasses import dataclass

from shvatka.infrastructure.db.config.models.db import DBConfigProperties


@dataclass
class DBConfig(DBConfigProperties):
    """A db config built from a ready-made url, as testcontainers hands it over."""

    uri_: str = ""

    @property
    def uri(self) -> str:
        return self.uri_
