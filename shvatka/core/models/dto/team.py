from __future__ import annotations

from dataclasses import InitVar, dataclass, field

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

    def __post_init__(self, chat: Chat | None, forum_team: ForumTeam | None) -> None:
        self._chat = chat
        self._forum_team = forum_team

    def is_captain(self, player_id: int) -> bool:
        """Whether this player captains the team.

        A team may have no captain at all — ``TeamDao.create_by_forum`` creates
        one that way — so the question is answered here rather than by
        dereferencing ``captain`` at each call site.
        """
        return self.captain is not None and self.captain.id == player_id

    def __eq__(self, other) -> bool:
        if not isinstance(other, Team):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"<Team id={self.id} name={self.name}>"

    def get_chat_id(self) -> int | None:
        if self._chat is None:
            return None
        return self._chat.tg_id

    def has_chat(self) -> bool:
        return self._chat is not None

    def has_forum_team(self) -> bool:
        return self._forum_team is not None
