import re

import pytest
from aiogram import Router
from aiogram_dialog.manager.message_manager import MessageManager
from aiogram_dialog.setup import collect_dialogs

from shvatka.tgbot.dialogs import setup as setup_dialogs_router
from shvatka.tgbot.dialogs.preview import render_dialogs_preview


@pytest.fixture(scope="module")
def dialogs_router() -> Router:
    # dialogs are module-level singletons, they can be attached to a router only once
    router = Router(name="preview")
    setup_dialogs_router(router, MessageManager())
    return router


def test_every_state_has_window(dialogs_router: Router) -> None:
    orphans = [
        state.state
        for dialog in collect_dialogs(dialogs_router)
        for state in dialog.states_group().__states__
        if state not in dialog.states()
    ]
    assert orphans == []


@pytest.mark.asyncio
async def test_render_preview(dialogs_router: Router, tmp_path) -> None:
    """Every window renders from its preview_data, without a bot or a database."""
    file = tmp_path / "preview.html"

    await render_dialogs_preview(dialogs_router, str(file))

    rendered = file.read_text(encoding="utf-8")
    windows = {
        state
        for dialog in collect_dialogs(dialogs_router)
        for state in (s.state for s in dialog.states())
    }
    assert windows
    for state in windows:
        assert f'id="{state}"' in rendered, f"{state} is missing in the preview"
    assert not re.search(r'<div class="text">\s*</div>', rendered), "empty window text rendered"
