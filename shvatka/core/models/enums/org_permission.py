import enum


class OrgPermission(enum.Enum):
    can_spy = enum.auto()
    can_see_log_keys = enum.auto()
    can_validate_waivers = enum.auto()
