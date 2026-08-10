from shvatka.infrastructure.db.config.models.db import DBConfigProperties


class DBConfig(DBConfigProperties):
    """A db config built from a ready-made url, as testcontainers hands it over.

    Not a dataclass on purpose: it inherits one whose fields come first, so a
    generated ``__init__`` would read the url as ``type``.
    """

    def __init__(self, uri_: str, echo: bool = False) -> None:
        super().__init__(echo=echo)
        self.uri_ = uri_

    @property
    def uri(self) -> str:
        return self.uri_
