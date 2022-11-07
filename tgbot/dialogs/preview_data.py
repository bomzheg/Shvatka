from datetime import datetime

from shvatka.models import dto
from shvatka.models.enums import GameStatus

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
)

PREVIEW_GAME = dto.Game(
    id=1,
    author=PREVIEW_AUTHOR,
    name="Схватка это чудо",
    start_at=datetime.utcnow(),
    status=GameStatus.getting_waivers,
    manage_token="1",
    published_channel_id=-100123435,
)
TIMES_PRESET = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
RENDERED_HINTS_PREVIEW = "0: 📃🪪\n10: 📃\n10: 📃\n15: 📃\n20: 📃\n25: 🪪\n30: 📡\n45: 📃"
