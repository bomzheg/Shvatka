from __future__ import annotations

from dataclasses import dataclass

from .chat import Chat
from .player import Player


@dataclass
class Team:
    id: int
    chat: Chat
    name: str
    description: str
    captain: Player
