import enum


class RequestType(enum.Enum):
    """A user-to-user request that needs a decision. Stored as its ``name`` (Text)."""

    team_join_invite = enum.auto()
    """A team manager invites a player to join their team."""
    team_join_request = enum.auto()
    """A player asks to join a team; answered by any authorized team member."""
    org_invite = enum.auto()
    """A game author invites a player to become an organizer."""


class RequestStatus(enum.Enum):
    pending = enum.auto()
    accepted = enum.auto()
    declined = enum.auto()
    cancelled = enum.auto()
    expired = enum.auto()
