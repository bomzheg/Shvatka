from dataclasses import dataclass

from .user import User


@dataclass
class Player:
    id: int
    user: User
