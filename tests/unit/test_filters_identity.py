"""Filters resolve who is acting from the container, not from middleware data.

They are wired through ``@inject``, which only works because aiogram passes
``dishka_container`` to anything it calls through a ``FilterObject`` — including
``BaseFilter`` subclasses. A filter that silently returned ``False`` here would
disable a command rather than fail, so drive them through the real machinery.
"""

from datetime import datetime, UTC
from typing import Any
from unittest.mock import AsyncMock

import pytest
from aiogram import Router
from aiogram.dispatcher.event.handler import FilterObject
from aiogram.types import Chat, Message
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.aiogram import CONTAINER_NAME

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums import GameStatus
from shvatka.tgbot.filters.can_be_author import can_be_author
from shvatka.tgbot.filters.game_status import GameStatusFilter
from shvatka.tgbot.filters.is_inviter import is_inviter
from shvatka.tgbot.filters.is_team import IsTeamFilter
from shvatka.tgbot.filters.team_player import TeamPlayerFilter
from shvatka.tgbot.utils.router import disable_router_on_game

PLAYER = dto.Player(id=1, can_be_author=True, is_dummy=False, username="harry")
NO_AUTHOR = dto.Player(id=2, can_be_author=False, is_dummy=False, username="ron")
TEAM = dto.Team(id=1, name="Gryffindor", captain=None, is_dummy=False, description=None)


def identity(
    player: dto.Player | None = PLAYER,
    team: dto.Team | None = None,
    team_player: dto.FullTeamPlayer | None = None,
) -> AsyncMock:
    idp = AsyncMock(IdentityProvider)
    idp.get_player.return_value = player
    idp.get_team.return_value = team
    idp.get_full_team_player.return_value = team_player
    return idp


def game(status: GameStatus) -> dto.Game:
    return dto.Game(
        id=1,
        author=PLAYER,
        name="Alice",
        status=status,
        manage_token="token",
        start_at=None,
        number=1,
        results=dto.GameResults(
            published_chanel_id=None, results_picture_file_id=None, keys_url=None
        ),
    )


def current_game(active: dto.Game | None) -> AsyncMock:
    provider = AsyncMock(CurrentGameProvider)
    provider.get_game.return_value = active
    return provider


async def call(
    filter_: Any, idp: AsyncMock, game_provider: AsyncMock | None = None, **kwargs: Any
) -> Any:
    class IdpProvider(Provider):
        scope = Scope.REQUEST

        @provide
        def idp(self) -> IdentityProvider:
            return idp

        @provide
        def current_game(self) -> CurrentGameProvider:
            return game_provider or current_game(None)

    container = make_async_container(IdpProvider())
    try:
        async with container() as request_container:
            return await FilterObject(filter_).call(
                None, **{CONTAINER_NAME: request_container, **kwargs}
            )
    finally:
        await container.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("player", "expected"),
    [(PLAYER, True), (NO_AUTHOR, False), (None, False)],
)
async def test_can_be_author(player, expected):
    assert await call(can_be_author, identity(player=player)) is expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("team", "is_team", "expected"),
    [(TEAM, True, True), (None, True, False), (None, False, True), (TEAM, False, False)],
)
async def test_is_team_filter(team, is_team, expected):
    assert await call(IsTeamFilter(is_team=is_team), identity(team=team)) is expected


@pytest.mark.asyncio
async def test_team_player_filter_without_team_is_false():
    assert await call(TeamPlayerFilter(), identity(team_player=None)) is False


@pytest.mark.asyncio
async def test_team_player_filter_checks_the_asked_permission():
    team_player = AsyncMock(dto.FullTeamPlayer)
    team_player.can_manage_players = True
    team_player.can_remove_players = False
    idp = identity(team_player=team_player)
    assert await call(TeamPlayerFilter(can_manage_players=True), idp) is True
    assert await call(TeamPlayerFilter(can_remove_players=True), idp) is False


@pytest.mark.asyncio
@pytest.mark.parametrize(("inviter_id", "expected"), [(PLAYER.id, True), (999, False)])
async def test_is_inviter(inviter_id, expected):
    callback_data = AsyncMock()
    callback_data.inviter_id = inviter_id
    assert await call(is_inviter, identity(), callback_data=callback_data) is expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("active_game", "expected"),
    [
        (None, True),
        (GameStatus.getting_waivers, True),
        (GameStatus.started, False),
        (GameStatus.finished, True),
    ],
)
async def test_disable_router_on_game(active_game, expected):
    """`GameStatusFilter(running=False)` gates almost every router in the bot."""
    provider = current_game(game(active_game) if active_game else None)
    assert await call(GameStatusFilter(running=False), identity(), provider) is expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("active_game", "expected"),
    [(None, False), (GameStatus.getting_waivers, False), (GameStatus.started, True)],
)
async def test_game_status_running(active_game, expected):
    provider = current_game(game(active_game) if active_game else None)
    assert await call(GameStatusFilter(running=True), identity(), provider) is expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("active_game", "expected"),
    [(None, False), (GameStatus.getting_waivers, True), (GameStatus.started, False)],
)
async def test_game_status_by_status(active_game, expected):
    provider = current_game(game(active_game) if active_game else None)
    filter_ = GameStatusFilter(status=GameStatus.getting_waivers)
    assert await call(filter_, identity(), provider) is expected


@pytest.mark.asyncio
async def test_game_status_active():
    assert await call(GameStatusFilter(active=True), identity(), current_game(None)) is False
    started = current_game(game(GameStatus.started))
    assert await call(GameStatusFilter(active=True), identity(), started) is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("active_game", "reaches_handlers"),
    [(None, True), (GameStatus.getting_waivers, True), (GameStatus.started, False)],
)
async def test_disable_router_on_game_through_root_filters(active_game, reaches_handlers):
    """`disable_router_on_game` registers *root* filters, not handler filters.

    Those run through `check_root_filters`, so an `@inject` that worked on a
    handler filter is not by itself proof that this path works — and this one
    gates nearly every router in the bot.
    """
    router = Router(name="test")
    disable_router_on_game(router)
    provider = current_game(game(active_game) if active_game else None)

    class Providers(Provider):
        scope = Scope.REQUEST

        @provide
        def idp(self) -> IdentityProvider:
            return identity()

        @provide
        def cg(self) -> CurrentGameProvider:
            return provider

    event = Message(
        message_id=1,
        date=datetime.now(tz=UTC),
        chat=Chat(id=1, type="private"),
        text="/start",
    )
    container = make_async_container(Providers())
    try:
        async with container() as request_container:
            passed, _ = await router.message.check_root_filters(
                event, **{CONTAINER_NAME: request_container}
            )
    finally:
        await container.close()
    assert bool(passed) is reaches_handlers
