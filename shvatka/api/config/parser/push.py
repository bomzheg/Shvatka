from dataclass_factory import Factory, Schema, NameStyle

from shvatka.api.config.models.push import PushConfig


def load_push(data: dict | None) -> PushConfig:
    if not data:
        return PushConfig()
    dcf = Factory(default_schema=Schema(name_style=NameStyle.kebab))
    return dcf.load(data, PushConfig)
