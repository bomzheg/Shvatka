from __future__ import annotations

from dataclasses import dataclass, field, InitVar

from .chat import Chat
from .player import Player


@dataclass
class Team:
    id: int
    _chat: Chat | None = field(init=False)
    chat: InitVar[Chat | None]
    name: str
    captain: Player
    is_dummy: bool
    description: str | None

    def __post_init__(self, chat: Chat | None):
        self._chat = chat

    def __eq__(self, other) -> bool:
        if not isinstance(other, Team):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def get_chat_id(self) -> int | None:
        if self.is_dummy:
            return None
        return self._chat.tg_id
