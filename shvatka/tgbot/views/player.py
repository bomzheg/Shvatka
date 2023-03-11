from shvatka.core.models import dto
from shvatka.core.utils.defaults_constants import EMOJI_BY_ROLE, DEFAULT_EMOJI


def get_emoji(pit: dto.TeamPlayer) -> str:
    if pit.emoji:
        return pit.emoji
    if pit.role:
        return EMOJI_BY_ROLE.get(pit.role.lower(), DEFAULT_EMOJI)
    return DEFAULT_EMOJI
