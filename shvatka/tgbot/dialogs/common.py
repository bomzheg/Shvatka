from typing import Any

from aiogram_dialog.widgets.text import Text, Const

from shvatka.core.views.texts import PERMISSION_EMOJI

BOOL_VIEW: dict[Any, Text] = {k: Const(v) for k, v in PERMISSION_EMOJI.items()}
