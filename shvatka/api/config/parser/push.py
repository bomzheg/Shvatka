from dataclass_factory import Factory

from shvatka.api.config.models.push import PushConfig


def load_push(data: dict | None, dcf: Factory) -> PushConfig:
    if not data:
        return PushConfig()
    return dcf.load(data, PushConfig)
