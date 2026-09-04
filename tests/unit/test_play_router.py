from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock

import pytest
from aiogram import Dispatcher
from aiogram.types import Chat, Message, User
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.aiogram import CONTAINER_NAME

from shvatka.core.games.interactors import CheckKeyInteractor
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus
from shvatka.tgbot.handlers.game import play
from shvatka.tgbot.main_factory import resolve_update_types

PLAYER = dto.Player(id=1, can_be_author=False, is_dummy=False, username="harry")
TEAM = dto.Team(id=1, name="Gryffindor", captain=None, is_dummy=False, description=None)
GAME_START = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)


def game(status: GameStatus = GameStatus.started) -> dto.Game:
    return dto.Game(
        id=1,
        author=PLAYER,
        name="Alice",
        status=status,
        manage_token="token",
        start_at=GAME_START,
        number=1,
        results=dto.GameResults(
            published_chanel_id=None, results_picture_file_id=None, keys_url=None
        ),
    )


def edited(text: str, sent_at: datetime) -> Message:
    return Message(
        message_id=1,
        date=sent_at,
        edit_date=int((GAME_START + timedelta(minutes=10)).timestamp()),
        chat=Chat(id=-100, type="supergroup"),
        from_user=User(id=1, is_bot=False, first_name="Harry"),
        text=text,
    )


async def feed(
    message: Message,
    status: GameStatus = GameStatus.started,
    update_type: str = "edited_message",
) -> Any:
    interactor = AsyncMock(CheckKeyInteractor)
    identity = AsyncMock(IdentityProvider)
    identity.get_team.return_value = TEAM
    identity.get_full_team_player.return_value = AsyncMock(dto.FullTeamPlayer)
    current_game = AsyncMock(CurrentGameProvider)
    current_game.get_game.return_value = game(status)

    class Providers(Provider):
        scope = Scope.REQUEST

        @provide
        def idp(self) -> IdentityProvider:
            return identity

        @provide
        def cg(self) -> CurrentGameProvider:
            return current_game

        @provide
        def check_key(self) -> CheckKeyInteractor:
            return interactor

    router = play.setup()
    container = make_async_container(Providers())
    try:
        async with container() as request_container:
            await router.propagate_event(
                update_type, message, **{CONTAINER_NAME: request_container}
            )
    finally:
        await container.close()
    return interactor


def test_edited_message_is_asked_for():
    dp = Dispatcher()
    dp.include_router(play.setup())
    assert "edited_message" in resolve_update_types(dp)


@pytest.mark.asyncio
async def test_edited_key_is_checked():
    interactor = await feed(edited("SHMONKEY", GAME_START + timedelta(minutes=5)))
    interactor.assert_awaited_once()
    assert interactor.await_args.kwargs["key"] == "SHMONKEY"


@pytest.mark.asyncio
async def test_edit_of_a_message_written_before_the_start_is_ignored():
    interactor = await feed(edited("SHMONKEY", GAME_START - timedelta(minutes=5)))
    interactor.assert_not_awaited()


@pytest.mark.asyncio
async def test_edit_without_a_key_is_ignored():
    interactor = await feed(edited("SH ONKEY", GAME_START + timedelta(minutes=5)))
    interactor.assert_not_awaited()


@pytest.mark.asyncio
async def test_edit_outside_a_running_game_is_ignored():
    interactor = await feed(
        edited("SHMONKEY", GAME_START + timedelta(minutes=5)),
        status=GameStatus.finished,
    )
    interactor.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_key_sent_as_a_new_message_is_still_checked():
    interactor = await feed(
        edited("SHMONKEY", GAME_START + timedelta(minutes=5)), update_type="message"
    )
    interactor.assert_awaited_once()
