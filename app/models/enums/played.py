import enum


class Played(str, enum.Enum):
    yes = 'yes'
    no = 'no'
    think = 'think'
    revoked = 'revoked'
    """не допущен капитаном"""
    not_allowed = 'not_allowed'
    """не допущен организаторами"""
