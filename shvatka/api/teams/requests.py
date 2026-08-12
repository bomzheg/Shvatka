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
class JoinCaptainedTeam:
    """Ask to join a team the caller captains.

    ``leave_current`` is the ui's checkbox: a player is in one team at a time, so
    entering the next one means leaving the current one in the same request.
    """

    leave_current: bool = False


@dataclass
class NewCaptain:
    player_id: int


@dataclass
class TeamPlayerSettings:
    role: str | None = None
    emoji: str | None = None
    permissions: dict[str, bool] | None = None
