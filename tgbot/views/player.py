from shvatka.models import dto
from shvatka.utils.defaults_constants import EMOJI_BY_ROLE, DEFAULT_EMOJI


def get_emoji(pit: dto.PlayerInTeam) -> str:
    if pit.emoji:
        return pit.emoji
    if pit.role:
        return EMOJI_BY_ROLE[pit.role]
    return DEFAULT_EMOJI
