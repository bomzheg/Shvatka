from __future__ import annotations

from dataclasses import InitVar, dataclass, field

from .chat import Chat
from .forum_team import ForumTeam
from .player import Player


@dataclass
class Team:
    id: int
    name: str
    is_dummy: bool
    description: str | None
    captain_id: int | None = None
    """Who captains the team, without loading them.

    ``teams.captain_id`` is on the row itself, so :meth:`is_captain` costs no
    join. Rendering the captain is what costs one — that is
    :class:`TeamWithCaptain`.
    """
    _chat: Chat | None = field(init=False)
    chat: InitVar[Chat | None] = field(default=None)
    _forum_team: ForumTeam | None = field(init=False)
    forum_team: InitVar[ForumTeam | None] = field(default=None)

    def __post_init__(self, chat: Chat | None, forum_team: ForumTeam | None) -> None:
        self._chat = chat
        self._forum_team = forum_team

    def is_captain(self, player_id: int) -> bool:
        """Whether this player captains the team.

        Answered from ``captain_id``, so it works on a team whose captain was
        never loaded — and a team may have no captain at all, since
        ``TeamDao.create_by_forum`` creates one that way.
        """
        return self.captain_id is not None and self.captain_id == player_id

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


@dataclass(eq=False)
class TeamWithCaptain(Team):
    """A team together with the player who captains it.

    Loading the captain joins ``players`` (and ``users`` behind it) onto every
    row carrying a team, and only the screens that show a captain by name need
    it: the team pages, the admin team tools and the bot's team card.
    Everything else takes a plain :class:`Team` and asks
    :meth:`Team.is_captain`.
    """

    captain: Player | None = None

    def __post_init__(self, chat: Chat | None, forum_team: ForumTeam | None) -> None:
        super().__post_init__(chat, forum_team)
        if self.captain_id is None:
            self.captain_id = self.captain.id if self.captain else None
