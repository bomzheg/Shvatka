from dataclasses import dataclass

import logging


logger = logging.getLogger(__name__)


@dataclass
class DBConfig:
    type: str = None
    connector: str = None
    host: str = None
    port: int = None
    login: str = None
    password: str = None
    name: str = None
    path: str = None

    @property
    def uri(self):
        if self.type in ('mysql', 'postgresql'):
            url = (
                f'{self.type}+{self.connector}://'
                f'{self.login}:{self.password}'
                f'@{self.host}:{self.port}/{self.name}'
            )
        elif self.type == 'sqlite':
            url = (
                f'{self.type}://{self.path}'
            )
        else:
            raise ValueError("DB_TYPE not mysql, sqlite or postgres")
        logger.debug(url)
        return url
