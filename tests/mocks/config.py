from shvatka.infrastructure.db.config.models.db import DBConfigProperties


class DBConfig(DBConfigProperties):
    def __init__(self, uri_: str, echo: bool = False) -> None:
        super().__init__(echo=echo)
        self.uri_ = uri_

    @property
    def uri(self) -> str:
        return self.uri_
