import enum


# noinspection PyArgumentList
class ChatType(enum.Enum):
    private = enum.auto()
    channel = enum.auto()
    group = enum.auto()
    supergroup = enum.auto()
