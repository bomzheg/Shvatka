from dataclasses import dataclass


@dataclass(frozen=True)
class PushConfig:
    vapid_public_key: str | None = None
    vapid_private_key: str | None = None
    vapid_claims_sub: str | None = None
    enabled: bool = False

    @property
    def is_configured(self) -> bool:
        return bool(
            self.enabled
            and self.vapid_public_key
            and self.vapid_private_key
            and self.vapid_claims_sub
        )
