from __future__ import annotations

from dataclasses import dataclass

from shvatka.models import db
from .chat import Chat
from .player import Player
from .user import User


@dataclass
class Team:
    id: int
    chat: Chat
    name: str
    description: str
    captain: Player

    @classmethod
    def from_db(cls, chat: Chat, team: db.Team) -> Team:
        return cls(
            id=team.id,
            chat=chat,
            name=team.name,
            description=team.description,
            captain=Player.from_db(
                player=team.captain,
                user=User.from_db(team.captain.user),
            ),
        )
