from typing import Any

from aiogram_dialog.api.internal import TextWidget
from aiogram_dialog.widgets.text import Const

from shvatka.core.views.texts import PERMISSION_EMOJI

BOOL_VIEW: dict[Any, TextWidget] = {k: Const(v) for k, v in PERMISSION_EMOJI.items()}
