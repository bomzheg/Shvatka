import enum


class Played(str, enum.Enum):
    yes = 'yes'
    no = 'no'
    think = 'think'
    revoked = 'revoked'
    not_allowed = 'not_allowed'
