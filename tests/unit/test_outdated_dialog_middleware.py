"""What happens when a dialog says the state it was opened for is gone.

The user must learn why the window stopped working, and the window itself must
go away - otherwise every next click hits the same dead state. See issue #339.
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from aiogram import Router
from aiogram.types import CallbackQuery, Chat, Message
from aiogram_dialog import DialogManager, setup_dialogs
from aiogram_dialog.manager.manager_middleware import MANAGER_KEY, ManagerMiddleware

from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.tgbot.dialogs import setup_outdated_dialogs
from shvatka.tgbot.dialogs.outdated import DialogOutdated, OutdatedDialogMiddleware
from tests.fixtures.user_constants import create_tg_user

NOTIFY = "Ты больше не состоишь в команде"


def create_callback() -> CallbackQuery:
    return CallbackQuery(
        id="1",
        data="whatever",
        chat_instance="--",
        from_user=create_tg_user(),
    )


def create_message() -> Message:
    return Message(
        message_id=1,
        date=datetime.fromtimestamp(1234567890, tz=tz_utc),
        chat=Chat(id=1, type="private"),
        from_user=create_tg_user(),
        text="whatever",
    )


def create_manager(has_context: bool = True) -> DialogManager:
    manager = AsyncMock(DialogManager)
    manager.has_context = lambda: has_context
    return manager


async def run(event: Any, manager: DialogManager | None) -> None:
    async def handler(_event: Any, _data: dict[str, Any]) -> None:
        raise DialogOutdated(NOTIFY, "player 1 is not in a team anymore")

    data: dict[str, Any] = {} if manager is None else {MANAGER_KEY: manager}
    await OutdatedDialogMiddleware()(handler, event, data)


@pytest.mark.asyncio
async def test_button_click_is_answered_with_alert_and_dialog_closed():
    manager = create_manager()

    with patch.object(CallbackQuery, "answer", new_callable=AsyncMock) as answer:
        await run(create_callback(), manager)

    answer.assert_awaited_once_with(NOTIFY, show_alert=True)
    manager.done.assert_awaited_once()


@pytest.mark.asyncio
async def test_typed_answer_is_replied_and_dialog_closed():
    manager = create_manager()

    with patch.object(Message, "answer", new_callable=AsyncMock) as answer:
        await run(create_message(), manager)

    answer.assert_awaited_once_with(NOTIFY)
    manager.done.assert_awaited_once()


@pytest.mark.asyncio
async def test_nothing_to_close_when_the_dialog_is_already_gone():
    manager = create_manager(has_context=False)

    with patch.object(CallbackQuery, "answer", new_callable=AsyncMock):
        await run(create_callback(), manager)

    manager.done.assert_not_awaited()


@pytest.mark.asyncio
async def test_user_is_still_notified_without_a_dialog_manager():
    with patch.object(CallbackQuery, "answer", new_callable=AsyncMock) as answer:
        await run(create_callback(), None)

    answer.assert_awaited_once_with(NOTIFY, show_alert=True)


@pytest.mark.parametrize("observer", ["callback_query", "message"])
def test_installed_inside_the_aiogram_dialog_manager(observer: str):
    """Without `dialog_manager` in the data there is nothing to close."""
    router = Router()
    setup_dialogs(router)
    setup_outdated_dialogs(router)

    middlewares = list(router.observers[observer].middleware)
    assert isinstance(middlewares[-1], OutdatedDialogMiddleware)
    assert any(isinstance(m, ManagerMiddleware) for m in middlewares[:-1])


@pytest.mark.asyncio
async def test_other_errors_are_not_swallowed():
    async def handler(_event: Any, _data: dict[str, Any]) -> None:
        raise ValueError("something else")

    with pytest.raises(ValueError, match="something else"):
        await OutdatedDialogMiddleware()(handler, create_callback(), {})
