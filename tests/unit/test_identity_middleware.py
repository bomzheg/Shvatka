from typing import Any, cast
from unittest.mock import AsyncMock

import pytest
from aiogram.types import Update
from dishka.integrations.aiogram import AiogramMiddlewareData

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.models import dto
from shvatka.tgbot.middlewares import LoadDataMiddleware
from shvatka.tgbot.services.identity import TgBotIdentityProvider
from shvatka.tgbot.utils.data import SHMiddlewareData
from tests.fixtures.chat_constants import create_tg_chat
from tests.fixtures.user_constants import create_tg_user


class ContainerMock:
    def __init__(self, identity: TgBotIdentityProvider, current_game: CurrentGameProvider) -> None:
        self._by_type: dict[Any, Any] = {
            TgBotIdentityProvider: identity,
            CurrentGameProvider: current_game,
        }

    async def get(self, type_: Any) -> Any:
        return self._by_type[type_]


async def run_middleware() -> tuple[AsyncMock, dict[str, Any]]:
    dao = AsyncMock()
    dao.user.upsert_user.return_value = dto.User(tg_id=666, first_name="Harry", is_bot=False)
    dao.chat.upsert_chat.return_value = None
    dao.player.upsert_player.return_value = None
    event = Update(update_id=1)
    data: dict[str, Any] = {
        "event_from_user": create_tg_user(),
        "event_chat": create_tg_chat(),
    }
    identity = TgBotIdentityProvider(
        dao=dao,
        event=event,
        aiogram_data=cast(AiogramMiddlewareData, data),
        superusers=AsyncMock(),
    )
    current_game = AsyncMock(CurrentGameProvider)
    current_game.get_game.return_value = None
    data["dishka_container"] = ContainerMock(identity, current_game)

    await LoadDataMiddleware()(AsyncMock(), event, cast(SHMiddlewareData, data))
    return dao, data


@pytest.mark.asyncio
async def test_user_and_chat_are_upserted_on_every_update():
    dao, _ = await run_middleware()
    dao.user.upsert_user.assert_awaited_once()
    dao.chat.upsert_chat.assert_awaited_once()


@pytest.mark.asyncio
async def test_player_is_created_for_a_user_seen_for_the_first_time():
    dao, _ = await run_middleware()
    dao.player.upsert_player.assert_awaited_once()


@pytest.mark.asyncio
async def test_identity_is_not_copied_into_middleware_data():
    _, data = await run_middleware()
    for key in ("user", "chat", "player", "team", "team_player"):
        assert key not in data
