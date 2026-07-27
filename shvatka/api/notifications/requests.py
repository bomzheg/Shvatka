from dataclasses import dataclass, field


@dataclass
class MarkNotificationsRead:
    ids: list[int] = field(default_factory=list)
