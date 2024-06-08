import enum


class Played(str, enum.Enum):
    yes = "yes"

    no = "no"

    think = "think"

    revoked = "revoked"
    """не допущен капитаном"""

    not_allowed = "not_allowed"
    """не допущен организаторами"""

    @property
    def can_play(self) -> bool:
        return self.value == Played.yes

    @property
    def is_deny(self) -> bool:
        return self.value == Played.no

    @property
    def cant_decide(self) -> bool:
        return self.value == Played.think

    @property
    def is_revoked(self) -> bool:
        return self.value == Played.revoked

    @property
    def is_not_allowed(self) -> bool:
        return self.value == Played.not_allowed
