from dataclasses import dataclass

from app.models.dto import User


@dataclass
class Player:
    id: int
    user: User
