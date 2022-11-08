from dataclasses import dataclass


@dataclass
class DBConfig:
    uri: str
    echo: bool = True
