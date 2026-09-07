from collections.abc import Sequence
from typing import cast

import pytest
from aiogram.types import InlineKeyboardButton
from aiogram_dialog.api.internal import ButtonVariant, RawKeyboard
from aiogram_dialog.tools.preview import FakeManager
from aiogram_dialog.widgets.kbd import Select, StubScroll
from aiogram_dialog.widgets.text import Format

from shvatka.tgbot.dialogs.paging import MAX_NUMBERED_PAGES, SmartPager, SmartScrollingGroup

HEIGHT = 10
GROUP_ID = "items_sg"


@pytest.fixture
def manager() -> FakeManager:
    manager = FakeManager()
    manager.reset_context()
    return manager


def _group() -> SmartScrollingGroup:
    return SmartScrollingGroup(
        Select(
            Format("{item}"),
            id="items",
            item_id_getter=str,
            items="items",
        ),
        id=GROUP_ID,
        width=1,
        height=HEIGHT,
    )


async def _render(manager: FakeManager, items: int, page: int = 0) -> RawKeyboard:
    manager.current_context().widget_data[GROUP_ID] = page
    return await _group().render_keyboard({"items": list(range(items))}, manager)


def _texts(row: Sequence[ButtonVariant]) -> list[str]:
    return [button.text for button in row]


def _callbacks(row: Sequence[ButtonVariant]) -> list[str | None]:
    return [cast("InlineKeyboardButton", button).callback_data for button in row]


@pytest.mark.asyncio
@pytest.mark.parametrize("items", [0, 1, 9, HEIGHT])
async def test_single_page_has_no_pager(manager: FakeManager, items: int) -> None:
    keyboard = await _render(manager, items)

    assert len(keyboard) == items
    assert _texts([button for row in keyboard for button in row]) == [
        str(item) for item in range(items)
    ]


@pytest.mark.asyncio
async def test_few_pages_are_numbered(manager: FakeManager) -> None:
    keyboard = await _render(manager, items=HEIGHT + 1)

    assert len(keyboard) == HEIGHT + 1  # a full page of items plus the pager
    assert _texts(keyboard[-1]) == ["[ 1 ]", "2"]
    assert _callbacks(keyboard[-1]) == [f"{GROUP_ID}:0", f"{GROUP_ID}:1"]


@pytest.mark.asyncio
async def test_last_numbered_page_count(manager: FakeManager) -> None:
    keyboard = await _render(manager, items=HEIGHT * MAX_NUMBERED_PAGES, page=2)

    assert _texts(keyboard[-1]) == ["1", "2", "[ 3 ]", "4", "5", "6", "7", "8"]


@pytest.mark.asyncio
async def test_many_pages_are_endless(manager: FakeManager) -> None:
    keyboard = await _render(manager, items=HEIGHT * MAX_NUMBERED_PAGES + 1, page=4)

    assert _texts(keyboard[-1]) == ["⏮", "◀️", "5/9", "▶️", "⏭"]
    assert _callbacks(keyboard[-1]) == [
        f"{GROUP_ID}:0",
        f"{GROUP_ID}:3",
        f"{GROUP_ID}:4",
        f"{GROUP_ID}:5",
        f"{GROUP_ID}:8",
    ]


@pytest.mark.asyncio
async def test_endless_pager_stops_at_the_edges(manager: FakeManager) -> None:
    pages = MAX_NUMBERED_PAGES + 1
    keyboard = await _render(manager, items=HEIGHT * pages, page=pages - 1)

    assert _texts(keyboard[-1]) == ["⏮", "◀️", "9/9", "▶️", "⏭"]
    assert _callbacks(keyboard[-1])[-2:] == [f"{GROUP_ID}:8", f"{GROUP_ID}:8"]


@pytest.mark.asyncio
async def test_page_out_of_range_shows_the_last_one(manager: FakeManager) -> None:
    keyboard = await _render(manager, items=HEIGHT + 1, page=42)

    assert _texts(keyboard[0]) == [str(HEIGHT)]
    assert _texts(keyboard[-1]) == ["1", "[ 2 ]"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("pages", "expected"),
    [
        (0, []),
        (1, []),
        (3, ["[ 1 ]", "2", "3"]),
        (MAX_NUMBERED_PAGES + 1, ["⏮", "◀️", "1/9", "▶️", "⏭"]),
    ],
)
async def test_pager_of_a_stub_scroll(
    manager: FakeManager, pages: int, expected: list[str]
) -> None:
    scroll = StubScroll(id="text", pages="pages")
    pager = SmartPager(scroll=scroll, id="text")

    keyboard = await pager.render_keyboard({"pages": pages}, manager)

    assert [text for row in keyboard for text in _texts(row)] == expected
