from datetime import datetime

from aiogram.fsm.state import State
from aiogram_dialog.widgets.kbd import Start, Cancel, SwitchTo
from aiogram_dialog.widgets.text import Const

from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus
from shvatka.core.utils.datetime_utils import tz_utc

PREVIEW_USER = dto.User(
    db_id=5,
    tg_id=900,
    username="bomzheg",
    first_name="Yuriy",
)

PREVIEW_AUTHOR = dto.Player(
    id=1,
    user=PREVIEW_USER,
    can_be_author=True,
    is_dummy=False,
)

PREVIEW_GAME = dto.PreviewGame(
    id=1,
    author=PREVIEW_AUTHOR,
    name="Схватка это чудо",
    start_at=datetime.now(tz=tz_utc),
    status=GameStatus.getting_waivers,
    manage_token="1",
    results=dto.GameResults(
        published_chanel_id=-100123435,
        results_picture_file_id=None,
        keys_url=None,
    ),
    number=1,
    levels_count=13,
)
TIMES_PRESET = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]


class PreviewStart(Start):
    def __init__(self, state: State):
        super().__init__(Const(""), "", state)


class PreviewSwitchTo(SwitchTo):
    def __init__(self, state: State):
        super().__init__(Const(""), "", state)
