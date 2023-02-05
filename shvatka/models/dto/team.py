from __future__ import annotations

from dataclasses import dataclass

from .chat import Chat
from .player import Player


@dataclass
class Team:
    id: int
    chat: Chat
    name: str
    captain: Player
    is_dummy: bool
    description: str | None

    def __eq__(self, other) -> bool:
        if not isinstance(other, Team):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
