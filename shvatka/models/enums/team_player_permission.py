import enum


class TeamPlayerPermission(enum.Enum):
    can_manage_waivers = enum.auto()
    can_manage_players = enum.auto()
    can_change_team_name = enum.auto()
    can_add_players = enum.auto()
    can_remove_players = enum.auto()
