from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pytest

from shvatka.core.games.admin_interactors import (
    AdminChangeGameStatusInteractor,
    AdminGamesListInteractor,
)
from shvatka.core.models import dto
from shvatka.core.models.dto import GameResults
from shvatka.core.models.enums import GameStatus
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc
from tests.fixtures.identity import MockIdentityProvider


def make_player(id_: int) -> dto.Player:
    return dto.Player(id=id_, can_be_author=True, is_dummy=False, username=f"player{id_}")


def make_game(
    status: GameStatus,
    *,
    id_: int = 10,
    start_at: datetime | None = None,
    number: int | None = None,
) -> dto.Game:
    return dto.Game(
        id=id_,
        author=make_player(1),
        name="my game",
        status=status,
        manage_token="token",
        start_at=start_at,
        number=number,
        results=GameResults(published_chanel_id=None, results_picture_file_id=None, keys_url=None),
    )


@dataclass
class FakeGameDao:
    game: dto.Game
    active_game: dto.Game | None = None
    listed: list[dto.Game] = field(default_factory=list)
    asked_for: list[tuple[GameStatus, ...]] = field(default_factory=list)
    cancelled: bool = False
    committed: int = 0
    max_number: int = 7
    level_time_ids: list[int] = field(default_factory=list)
    purged: list[str] = field(default_factory=list)
    purged_timers_for: list[int] | None = None

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return self.game

    async def get_by_statuses(self, statuses) -> list[dto.Game]:
        self.asked_for.append(tuple(statuses))
        return self.listed

    async def get_active_game(self) -> dto.Game | None:
        return self.active_game

    async def set_status(self, game: dto.Game, status: GameStatus) -> None:
        game.status = status

    async def set_completed(self, game: dto.Game) -> None:
        game.status = GameStatus.complete

    async def set_number(self, game: dto.Game, number: int) -> None:
        game.number = number

    async def get_max_number(self) -> int:
        return self.max_number

    async def cancel_start(self, game: dto.Game) -> None:
        self.cancelled = True

    async def get_level_time_ids(self, game: dto.Game) -> list[int]:
        return list(self.level_time_ids)

    async def delete_timers(self, level_time_ids) -> None:
        self.purged.append("timers")
        self.purged_timers_for = list(level_time_ids)

    async def delete_typed_keys(self, game: dto.Game) -> None:
        self.purged.append("keys")

    async def delete_events(self, game: dto.Game) -> None:
        self.purged.append("events")

    async def delete_level_times(self, game: dto.Game) -> None:
        self.purged.append("level_times")

    async def commit(self) -> None:
        self.committed += 1


@dataclass
class FakeScheduler:
    calls: list[str] = field(default_factory=list)

    async def cancel_scheduled_game(self, game: dto.Game) -> None:
        self.calls.append("cancel")


def admin_identity() -> MockIdentityProvider:
    admin = make_player(99)
    return MockIdentityProvider(player=admin, superuser=admin)


@pytest.mark.asyncio
async def test_returns_a_waivers_game_to_its_author():
    game = make_game(GameStatus.getting_waivers)
    dao = FakeGameDao(game=game)
    scheduler = FakeScheduler()
    interactor = AdminChangeGameStatusInteractor(dao=dao, scheduler=scheduler)

    result = await interactor(
        game_id=game.id,
        status=GameStatus.underconstruction,
        identity=admin_identity(),
    )

    assert result.status == GameStatus.underconstruction
    assert dao.committed == 1


@pytest.mark.asyncio
async def test_leaving_the_active_statuses_takes_the_planned_start_with_it():
    start_at = datetime.now(tz=tz_utc) + timedelta(days=1)
    game = make_game(GameStatus.getting_waivers, start_at=start_at)
    dao = FakeGameDao(game=game)
    scheduler = FakeScheduler()
    interactor = AdminChangeGameStatusInteractor(dao=dao, scheduler=scheduler)

    result = await interactor(
        game_id=game.id,
        status=GameStatus.underconstruction,
        identity=admin_identity(),
    )

    assert result.start_at is None
    assert dao.cancelled is True
    assert scheduler.calls == ["cancel"]


@pytest.mark.asyncio
async def test_a_game_still_being_written_is_not_found():
    for status in (GameStatus.underconstruction, GameStatus.ready):
        game = make_game(status)
        interactor = AdminChangeGameStatusInteractor(
            dao=FakeGameDao(game=game), scheduler=FakeScheduler()
        )

        with pytest.raises(exceptions.GameNotFound):
            await interactor(
                game_id=game.id,
                status=GameStatus.getting_waivers,
                identity=admin_identity(),
            )


@pytest.mark.asyncio
async def test_another_active_game_blocks_the_move_into_the_active_statuses():
    game = make_game(GameStatus.complete)
    dao = FakeGameDao(game=game, active_game=make_game(GameStatus.started, id_=11))
    interactor = AdminChangeGameStatusInteractor(dao=dao, scheduler=FakeScheduler())

    with pytest.raises(exceptions.AnotherGameIsActive):
        await interactor(
            game_id=game.id,
            status=GameStatus.started,
            identity=admin_identity(),
        )
    assert dao.committed == 0


@pytest.mark.asyncio
async def test_completing_gives_the_game_its_number():
    game = make_game(GameStatus.finished)
    dao = FakeGameDao(game=game, max_number=7)
    interactor = AdminChangeGameStatusInteractor(dao=dao, scheduler=FakeScheduler())

    result = await interactor(
        game_id=game.id,
        status=GameStatus.complete,
        identity=admin_identity(),
    )

    assert result.is_complete()
    assert result.number == 8


@pytest.mark.asyncio
async def test_a_game_that_already_has_a_number_keeps_it():
    game = make_game(GameStatus.finished, number=3)
    dao = FakeGameDao(game=game, max_number=7)
    interactor = AdminChangeGameStatusInteractor(dao=dao, scheduler=FakeScheduler())

    result = await interactor(
        game_id=game.id,
        status=GameStatus.complete,
        identity=admin_identity(),
    )

    assert result.number == 3


@pytest.mark.asyncio
async def test_a_game_that_is_not_finished_cant_be_completed():
    game = make_game(GameStatus.started)
    dao = FakeGameDao(game=game)
    interactor = AdminChangeGameStatusInteractor(dao=dao, scheduler=FakeScheduler())

    with pytest.raises(exceptions.GameNotFinished):
        await interactor(
            game_id=game.id,
            status=GameStatus.complete,
            identity=admin_identity(),
        )


@pytest.mark.asyncio
async def test_only_a_superuser_may_change_a_status():
    game = make_game(GameStatus.getting_waivers)
    interactor = AdminChangeGameStatusInteractor(
        dao=FakeGameDao(game=game), scheduler=FakeScheduler()
    )

    with pytest.raises(exceptions.NotAuthorizedForAdmin):
        await interactor(
            game_id=game.id,
            status=GameStatus.underconstruction,
            identity=MockIdentityProvider(player=make_player(2)),
        )


@pytest.mark.asyncio
async def test_the_list_asks_only_for_games_an_admin_may_see():
    dao = FakeGameDao(game=make_game(GameStatus.started))
    interactor = AdminGamesListInteractor(dao=dao)

    await interactor(admin_identity())

    (statuses,) = dao.asked_for
    assert set(statuses) == {
        GameStatus.getting_waivers,
        GameStatus.started,
        GameStatus.finished,
        GameStatus.complete,
    }


@pytest.mark.asyncio
async def test_only_a_superuser_may_list_the_games():
    interactor = AdminGamesListInteractor(dao=FakeGameDao(game=make_game(GameStatus.started)))

    with pytest.raises(exceptions.NotAuthorizedForAdmin):
        await interactor(MockIdentityProvider(player=make_player(2)))


@pytest.mark.asyncio
async def test_rewinding_a_played_game_can_take_its_run_with_it():
    game = make_game(GameStatus.started)
    dao = FakeGameDao(game=game, level_time_ids=[4, 5, 6])
    interactor = AdminChangeGameStatusInteractor(dao=dao, scheduler=FakeScheduler())

    await interactor(
        game_id=game.id,
        status=GameStatus.getting_waivers,
        identity=admin_identity(),
        purge_runtime=True,
    )

    # the order is the one the foreign keys allow, and timers are addressed by
    # the level time ids read before anything was dropped
    assert dao.purged == ["timers", "keys", "events", "level_times"]
    assert dao.purged_timers_for == [4, 5, 6]
    assert dao.committed == 1


@pytest.mark.asyncio
async def test_a_status_change_leaves_the_run_alone_by_default():
    game = make_game(GameStatus.finished)
    dao = FakeGameDao(game=game, level_time_ids=[1])
    interactor = AdminChangeGameStatusInteractor(dao=dao, scheduler=FakeScheduler())

    await interactor(
        game_id=game.id,
        status=GameStatus.getting_waivers,
        identity=admin_identity(),
    )

    assert dao.purged == []


@pytest.mark.parametrize(
    ("from_", "to"),
    [
        # forward, not back: the game is going on, its history is not the panel's
        (GameStatus.getting_waivers, GameStatus.started),
        (GameStatus.started, GameStatus.finished),
        (GameStatus.finished, GameStatus.complete),
        # a game that never ran has nothing to sweep, and asking is a mistake
        (GameStatus.getting_waivers, GameStatus.underconstruction),
    ],
)
@pytest.mark.asyncio
async def test_the_purge_is_refused_on_a_move_that_is_not_a_rewind(from_, to):
    game = make_game(from_)
    dao = FakeGameDao(game=game, level_time_ids=[1])
    interactor = AdminChangeGameStatusInteractor(dao=dao, scheduler=FakeScheduler())

    with pytest.raises(exceptions.GameStatusError):
        await interactor(
            game_id=game.id,
            status=to,
            identity=admin_identity(),
            purge_runtime=True,
        )

    # refused before anything was written — not the status, not a single row
    assert game.status == from_
    assert dao.purged == []
    assert dao.committed == 0


@pytest.mark.asyncio
async def test_only_a_superuser_may_purge_a_run():
    game = make_game(GameStatus.finished)
    dao = FakeGameDao(game=game, level_time_ids=[1])
    interactor = AdminChangeGameStatusInteractor(dao=dao, scheduler=FakeScheduler())

    with pytest.raises(exceptions.NotAuthorizedForAdmin):
        await interactor(
            game_id=game.id,
            status=GameStatus.getting_waivers,
            identity=MockIdentityProvider(player=make_player(2)),
            purge_runtime=True,
        )
    assert dao.purged == []
