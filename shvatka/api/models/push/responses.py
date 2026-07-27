from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PushConfigResponse:
    enabled: bool
    public_key: str | None
