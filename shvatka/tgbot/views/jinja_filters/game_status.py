from shvatka.core.models import enums
from shvatka.core.models.enums.game_status import status_desc


def to_readable_name(status: enums.GameStatus) -> str:
    return status_desc[status]
