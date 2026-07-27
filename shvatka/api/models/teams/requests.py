from dataclasses import dataclass


@dataclass
class NewTeam:
    name: str
    description: str | None = None


@dataclass
class TeamSettings:
    name: str | None = None
    description: str | None = None


@dataclass
class JoinTeam:
    player_id: int
    role: str | None = None
    emoji: str | None = None


@dataclass
class TeamPlayerSettings:
    role: str | None = None
    emoji: str | None = None
    permissions: dict[str, bool] | None = None
