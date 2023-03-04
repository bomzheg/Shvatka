from __future__ import annotations

from dataclasses import dataclass, field, InitVar

from .chat import Chat
from .forum_team import ForumTeam
from .player import Player


@dataclass
class Team:
    id: int
    name: str
    captain: Player | None
    is_dummy: bool
    description: str | None
    _chat: Chat | None = field(init=False)
    chat: InitVar[Chat | None] = field(default=None)
    _forum_team: ForumTeam | None = field(init=False)
    forum_team: InitVar[ForumTeam | None] = field(default=None)

    def __post_init__(self, chat: Chat | None, forum_team: ForumTeam | None):
        self._chat = chat
        self._forum_team = forum_team

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
