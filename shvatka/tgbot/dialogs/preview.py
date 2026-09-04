from collections.abc import Iterable
from pathlib import Path

from aiogram_dialog import Dialog
from aiogram_dialog.tools.preview import FakeManager, render_dialog
from aiogram_dialog.widgets.text.jinja import default_env
from jinja2 import Environment, PackageLoader, select_autoescape

from shvatka.tgbot.views.jinja_filters import get_filters

DEFAULT_PREVIEW_FILE = "out/shvatka-dialogs-preview.html"


async def render_dialogs_preview(
    dialogs: Iterable[Dialog], filename: str = DEFAULT_PREVIEW_FILE
) -> None:
    # There is neither Bot nor Dispatcher while rendering a preview, so the Jinja
    # widget falls back to the library-wide default environment. Teach that one
    # our filters, otherwise every window using them fails to render.
    default_env.filters.update(get_filters())
    manager = FakeManager()
    rendered = [
        await render_dialog(
            manager=manager,
            group=dialog.states_group(),
            dialog=dialog,
            simulate_events=False,
        )
        for dialog in dialogs
    ]
    env = Environment(
        loader=PackageLoader("aiogram_dialog.tools"),
        autoescape=select_autoescape(),
    )
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(env.get_template("message.html").render(dialogs=rendered), encoding="utf-8")
