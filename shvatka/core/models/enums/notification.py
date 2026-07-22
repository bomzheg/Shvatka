import enum


class NotificationType(enum.Enum):
    """What happened. Stored as its ``name`` (Text) so new types need no migration."""

    player_joined_team = enum.auto()
    player_left_team = enum.auto()
    team_renamed = enum.auto()
    org_added = enum.auto()
    game_schedule_changed = enum.auto()
    season_schedule_changed = enum.auto()
    team_join_invite = enum.auto()
    team_join_request = enum.auto()
    org_invite = enum.auto()
    team_merge_request = enum.auto()
    player_merge_request = enum.auto()
    promotion_invite = enum.auto()
    request_accepted = enum.auto()
    request_declined = enum.auto()


class NotificationSeverity(enum.Enum):
    """How much a notification matters. Drives UI emphasis and push urgency."""

    low = enum.auto()
    normal = enum.auto()
    important = enum.auto()
