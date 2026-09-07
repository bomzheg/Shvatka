from collections.abc import Sequence
from itertools import chain

from aiogram_dialog.api.internal import ButtonVariant, RawKeyboard
from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.common import OnPageChangedVariants, Scroll, WhenCondition
from aiogram_dialog.widgets.kbd import Keyboard, NumberedPager, ScrollingGroup, SwitchPage
from aiogram_dialog.widgets.kbd.pager import DEFAULT_PAGER_ID, BasePager, PageDirection
from aiogram_dialog.widgets.text import Const, Format

MAX_NUMBERED_PAGES = 8
"""Above this many pages a button per page stops being worth its width."""

MAX_BUTTONS_IN_ROW = 8
"""Telegram squeezes a wider row until the labels are unreadable."""

FIRST_PAGE_TEXT = Const("⏮")
PREV_PAGE_TEXT = Const("◀️")
CURRENT_PAGE_TEXT = Format("{current_page1}/{pages}")
NEXT_PAGE_TEXT = Const("▶️")
LAST_PAGE_TEXT = Const("⏭")


class _SwitchPage(SwitchPage):
    """`SwitchPage` rendered from an already counted page count."""

    async def render_page(
        self,
        data: dict,
        pages: int,
        current_page: int,
        manager: DialogManager,
    ) -> RawKeyboard:
        target_page = await self._get_target_page(current_page, pages)
        button_data = await self._prepare_data(
            data=data,
            target_page=target_page,
            current_page=current_page,
            pages=pages,
        )
        return await Keyboard.render_keyboard(self, button_data, manager)


class _NumberedPages(NumberedPager):
    """`NumberedPager` rendered from an already counted page count."""

    async def render_pages(
        self,
        data: dict,
        pages: int,
        current_page: int,
        manager: DialogManager,
    ) -> RawKeyboard:
        pager_data = await self._prepare_data(
            data=data,
            current_page=current_page,
            pages=pages,
        )
        return await Keyboard.render_keyboard(self, pager_data, manager)


class SmartPager(BasePager):
    """
    A pager whose shape follows the number of pages.

    * one page (or none at all) — nothing is rendered, the list speaks for itself;
    * up to `max_numbered_pages` — every page gets a button of its own, so any of
      them is one tap away;
    * more than that — the endless `⏮ ◀️ 3/42 ▶️ ⏭` row.

    Works with any scroll: a `ScrollingGroup` (see `SmartScrollingGroup`, which
    already carries one) or a `StubScroll` counting pages of text.
    """

    def __init__(
        self,
        scroll: str | Scroll | None,
        id: str = DEFAULT_PAGER_ID,  # noqa: A002
        max_numbered_pages: int = MAX_NUMBERED_PAGES,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(id=id, scroll=scroll, when=when)
        self.max_numbered_pages = max_numbered_pages
        # every button of every mode switches the same scroll to a page number,
        # so they all share one widget id — and one callback handler with it
        self.numbered = _NumberedPages(scroll=scroll, id=id, length=MAX_BUTTONS_IN_ROW)
        self.endless: Sequence[_SwitchPage] = [
            _SwitchPage(page=direction, scroll=scroll, id=id, text=text)
            for direction, text in (
                (PageDirection.FIRST, FIRST_PAGE_TEXT),
                (PageDirection.PREV, PREV_PAGE_TEXT),
                (PageDirection.IGNORE, CURRENT_PAGE_TEXT),
                (PageDirection.NEXT, NEXT_PAGE_TEXT),
                (PageDirection.LAST, LAST_PAGE_TEXT),
            )
        ]

    async def _render_keyboard(self, data: dict, manager: DialogManager) -> RawKeyboard:
        scroll = self._find_scroll(manager)
        return await self.render_pages(
            data=data,
            pages=await scroll.get_page_count(data),
            current_page=await scroll.get_page(),
            manager=manager,
        )

    async def render_pages(
        self,
        data: dict,
        pages: int,
        current_page: int,
        manager: DialogManager,
    ) -> RawKeyboard:
        """
        Render the pager for a page count someone else has already got.

        Counting pages of a `ScrollingGroup` means rendering all of its buttons,
        so the owner of the scroll passes the number it knows instead of letting
        every page button ask for it again.
        """
        if pages <= 1:
            return []
        current_page = min(current_page, pages - 1)
        if pages <= self.max_numbered_pages:
            return await self.numbered.render_pages(data, pages, current_page, manager)
        row: list[ButtonVariant] = []
        for switch in self.endless:
            rendered = await switch.render_page(data, pages, current_page, manager)
            row.extend(chain.from_iterable(rendered))
        return [row]


class SmartScrollingGroup(ScrollingGroup):
    """`ScrollingGroup` showing a `SmartPager` instead of the fixed five-button pager."""

    def __init__(
        self,
        *buttons: Keyboard,
        id: str,  # noqa: A002
        width: int | None = None,
        height: int = 0,
        when: WhenCondition = None,
        on_page_changed: OnPageChangedVariants = None,
        max_numbered_pages: int = MAX_NUMBERED_PAGES,
    ) -> None:
        super().__init__(
            *buttons,
            id=id,
            width=width,
            height=height,
            when=when,
            on_page_changed=on_page_changed,
            hide_pager=True,
        )
        # the pager shares the group's widget id, so switching a page arrives as
        # this group's own callback — see `ScrollingGroup._process_item_callback`
        self.pager = SmartPager(scroll=self, id=id, max_numbered_pages=max_numbered_pages)

    async def _render_keyboard(self, data: dict, manager: DialogManager) -> RawKeyboard:
        keyboard = await self._render_contents(data, manager)
        pages = self._get_page_count(keyboard)
        # `ScrollingGroup._render_page` counts the pages once more, and it is the
        # count the pager needs anyway — so cut the page out here instead
        current_page = min(await self.get_page(manager), max(pages - 1, 0))
        offset = current_page * self.height
        page_keyboard = keyboard[offset : offset + self.height]
        pager = await self.pager.render_pages(
            data=data,
            pages=pages,
            current_page=current_page,
            manager=manager,
        )
        return page_keyboard + pager
