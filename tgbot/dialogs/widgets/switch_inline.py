from typing import Optional, Union, Callable, Dict, List

from aiogram.types import InlineKeyboardButton
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Keyboard
from aiogram_dialog.widgets.text import Text


class SwitchInlineQuery(Keyboard):
    def __init__(
        self,
        text: Text,
        switch_inline_query: Text,
        id: Optional[str] = None,
        when: Union[str, Callable, None] = None,
    ):
        super().__init__(id=id, when=when)
        self.text = text
        self.switch_inline = switch_inline_query

    async def _render_keyboard(
        self,
        data: Dict,
        manager: DialogManager,
    ) -> List[List[InlineKeyboardButton]]:
        return [
            [
                InlineKeyboardButton(
                    text=await self.text.render_text(data, manager),
                    switch_inline_query=await self.switch_inline.render_text(
                        data, manager,
                    ),
                ),
            ],
        ]
