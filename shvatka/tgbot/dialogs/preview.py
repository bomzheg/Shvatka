"""Rendering every dialog window into one static html page.

The preview never touches a bot, a database or the DI container: windows are
rendered from their ``preview_data`` (see :mod:`shvatka.tgbot.dialogs.preview_data`).
"""

from pathlib import Path

from aiogram import Router
from aiogram_dialog.tools.preview import render_preview
from aiogram_dialog.widgets.text.jinja import default_env

from shvatka.tgbot.views.jinja_filters import get_filters

DEFAULT_PREVIEW_FILE = "out/shvatka-dialogs-preview.html"


async def render_dialogs_preview(router: Router, filename: str = DEFAULT_PREVIEW_FILE) -> None:
    # There is neither Bot nor Dispatcher while rendering a preview, so the Jinja
    # widget falls back to the library-wide default environment. Teach that one
    # our filters, otherwise every window using them fails to render.
    default_env.filters.update(get_filters())
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    await render_preview(router, filename)
