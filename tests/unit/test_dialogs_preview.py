import re

import pytest
from aiogram_dialog import Dialog

from shvatka.tgbot.dialogs import collect_all_dialogs
from shvatka.tgbot.dialogs.preview import render_dialogs_preview


@pytest.fixture
def dialogs() -> list[Dialog]:
    return collect_all_dialogs()


def test_every_state_has_window(dialogs: list[Dialog]) -> None:
    orphans = [
        state.state
        for dialog in dialogs
        for state in dialog.states_group().__states__
        if state not in dialog.states()
    ]
    assert orphans == []


@pytest.mark.asyncio
async def test_render_preview(dialogs: list[Dialog], tmp_path) -> None:
    """Every window renders from its preview_data, without a bot or a database."""
    file = tmp_path / "preview.html"

    await render_dialogs_preview(dialogs, str(file))

    rendered = file.read_text(encoding="utf-8")
    windows = {state.state for dialog in dialogs for state in dialog.states()}
    assert windows
    for state in windows:
        assert f'id="{state}"' in rendered, f"{state} is missing in the preview"
    assert not re.search(r'<div class="text">\s*</div>', rendered), "empty window text rendered"
