from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PushKeys:
    p256dh: str
    auth: str


@dataclass(frozen=True, slots=True)
class PushSubscription:
    endpoint: str
    keys: PushKeys
