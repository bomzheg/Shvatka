from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pytest

from shvatka.core.games.editor_interactors import (
    ChangeGameStatusInteractor,
    PlanGameStartInteractor,
)
from shvatka.core.models import dto
from shvatka.core.models.dto import GameResults
from shvatka.core.models.enums import GameStatus
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import DATETIME_FORMAT, tz_game, tz_utc
from shvatka.core.views.game import GameLogEvent, GameLogType, GameLogWriter
from tests.fixtures.identity import MockIdentityProvider


def make_player(id_: int) -> dto.Player:
    return dto.Player(id=id_, can_be_author=True, is_dummy=False, username=f"player{id_}")


def make_game(author: dto.Player, status: GameStatus) -> dto.Game:
    return dto.Game(
        id=10,
        author=author,
        name="my game",
        status=status,
        manage_token="token",
        start_at=None,
        number=None,
        results=GameResults(published_chanel_id=None, results_picture_file_id=None, keys_url=None),
    )


class RecordingLogWriter(GameLogWriter):
    def __init__(self) -> None:
        self.calls: list[GameLogEvent] = []

    async def log(self, log_event: GameLogEvent) -> None:
        self.calls.append(log_event)


@dataclass
class FakeGameDao:
    """In-memory stand-in covering the game-edit DAO protocols we need."""

    game: dto.Game
    active_game: dto.Game | None = None
    started: bool = False
    committed: int = 0
    start_at: datetime | None = None
    cancelled: bool = False

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return self.game

    async def get_active_game(self) -> dto.Game | None:
        return self.active_game

    async def start_waivers(self, game: dto.Game) -> None:
        self.started = True

    async def set_start_at(self, game: dto.Game, start_at: datetime) -> None:
        self.start_at = start_at

    async def cancel_start(self, game: dto.Game) -> None:
        self.cancelled = True

    async def commit(self) -> None:
        self.committed += 1


@dataclass
class FakeScheduler:
    calls: list[str] = field(default_factory=list)

    async def cancel_scheduled_game(self, game: dto.Game) -> None:
        self.calls.append("cancel")

    async def plain_prepare(self, game: dto.Game) -> None:
        self.calls.append("prepare")

    async def plain_start(self, game: dto.Game) -> None:
        self.calls.append("start")


@pytest.mark.asyncio
async def test_change_status_to_waivers_writes_game_log():
    author = make_player(1)
    game = make_game(author, GameStatus.ready)
    dao = FakeGameDao(game=game)
    game_log = RecordingLogWriter()
    interactor = ChangeGameStatusInteractor(
        getter=dao, waiver_starter=dao, completer=dao, game_log=game_log
    )

    await interactor(
        game_id=game.id,
        status=GameStatus.getting_waivers,
        identity=MockIdentityProvider(player=author),
    )

    assert dao.started is True
    assert game_log.calls == [GameLogEvent(GameLogType.GAME_WAIVERS_STARTED, {"game": game.name})]


@pytest.mark.asyncio
async def test_change_status_unsupported_does_not_write_game_log():
    author = make_player(1)
    game = make_game(author, GameStatus.ready)
    dao = FakeGameDao(game=game)
    game_log = RecordingLogWriter()
    interactor = ChangeGameStatusInteractor(
        getter=dao, waiver_starter=dao, completer=dao, game_log=game_log
    )

    with pytest.raises(exceptions.CantEditGame):
        await interactor(
            game_id=game.id,
            status=GameStatus.started,
            identity=MockIdentityProvider(player=author),
        )
    assert game_log.calls == []


@pytest.mark.asyncio
async def test_plan_start_writes_game_log():
    author = make_player(1)
    game = make_game(author, GameStatus.ready)
    dao = FakeGameDao(game=game)
    scheduler = FakeScheduler()
    game_log = RecordingLogWriter()
    interactor = PlanGameStartInteractor(
        getter=dao, dao=dao, scheduler=scheduler, game_log=game_log
    )
    start_at = datetime.now(tz=tz_utc) + timedelta(days=1)

    await interactor(
        game_id=game.id,
        start_at=start_at,
        identity=MockIdentityProvider(player=author),
    )

    assert dao.start_at == start_at
    assert game_log.calls == [
        GameLogEvent(
            GameLogType.GAME_PLANED,
            {"game": game.name, "at": start_at.astimezone(tz_game).strftime(DATETIME_FORMAT)},
        )
    ]


@pytest.mark.asyncio
async def test_cancel_planned_start_does_not_write_game_log():
    author = make_player(1)
    game = make_game(author, GameStatus.getting_waivers)
    dao = FakeGameDao(game=game)
    scheduler = FakeScheduler()
    game_log = RecordingLogWriter()
    interactor = PlanGameStartInteractor(
        getter=dao, dao=dao, scheduler=scheduler, game_log=game_log
    )

    await interactor(
        game_id=game.id,
        start_at=None,
        identity=MockIdentityProvider(player=author),
    )

    assert dao.cancelled is True
    assert game_log.calls == []
