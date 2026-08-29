"""Resending a running level's messages from the admin panel (shvatka-ui#185).

Telegram loses a message and a team is left without its puzzle. The panel can
put that right — and these pin down that it does so blind: what the admin gets
back says which teams were covered and nothing about where any of them is.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pytest

from shvatka.core.games.admin_interactors import AdminResendCurrentLevelInteractor
from shvatka.core.models import dto
from shvatka.core.models.dto import GameResults, action, hints, scn
from shvatka.core.models.enums import GameStatus
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.views.game import SendHint, SendPuzzle, ShowTasks
from tests.fixtures.identity import MockIdentityProvider

AUTHOR = dto.Player(id=1, can_be_author=True, is_dummy=False, username="author")


def make_team(id_: int) -> dto.Team:
    return dto.Team(
        id=id_,
        name=f"team{id_}",
        captain=None,
        is_dummy=False,
        description=None,
    )


def make_level(number: int, hint_times: list[int]) -> dto.GamedLevel:
    scenario = scn.LevelScenario(
        id=f"level{number}",
        time_hints=scn.HintsList(
            [
                hints.TimeHint(time=time, hint=[hints.TextHint(text=f"hint {time}")])
                for time in hint_times
            ]
        ),
        conditions=scn.Conditions([action.KeyWinCondition({f"SH{number}"})]),
        __model_version__=1,
    )
    return dto.GamedLevel(
        db_id=100 + number,
        name_id=f"level{number}",
        author=AUTHOR,
        scenario=scenario,
        game_id=10,
        number_in_game=number,
    )


def make_game(status: GameStatus = GameStatus.started) -> dto.FullGame:
    return dto.FullGame(
        id=10,
        author=AUTHOR,
        name="my game",
        status=status,
        manage_token="token",
        start_at=datetime.now(tz=tz_utc) - timedelta(hours=1),
        number=None,
        results=GameResults(published_chanel_id=None, results_picture_file_id=None, keys_url=None),
        levels=[make_level(0, [0, 10, 20]), make_level(1, [0, 5])],
    )


@dataclass
class FakeResenderDao:
    """In-memory stand-in for ``AdminLevelResender``."""

    teams: list[dto.Team]
    level_times: dict[int, dto.LevelTime] = field(default_factory=dict)

    async def get_played_teams(self, game: dto.Game) -> list[dto.Team]:
        return self.teams

    async def get_current_level_time(self, team: dto.Team, game: dto.Game) -> dto.LevelTime:
        try:
            return self.level_times[team.id]
        except KeyError as e:
            raise exceptions.TeamCurrentLevelNotFound(team=team, game=game) from e


@dataclass
class FakeSender:
    shown: list[ShowTasks] = field(default_factory=list)

    async def show_later(self, tasks: ShowTasks) -> None:
        self.shown.append(tasks)


@dataclass
class FakeCurrentGame:
    game: dto.FullGame | None

    async def get_full_game(self) -> dto.FullGame | None:
        return self.game

    async def get_required_full_game(self) -> dto.FullGame:
        if self.game is None:
            raise exceptions.HaveNotActiveGame
        return self.game


def level_time(id_: int, team: dto.Team, game: dto.Game, number: int, minutes_ago: int):
    return dto.LevelTime(
        id=id_,
        game=game,
        team=team,
        level_number=number,
        start_at=datetime.now(tz=tz_utc) - timedelta(minutes=minutes_ago),
    )


def admin_identity() -> MockIdentityProvider:
    admin = dto.Player(id=99, can_be_author=True, is_dummy=False, username="admin")
    return MockIdentityProvider(player=admin, superuser=admin)


def build(game: dto.FullGame, dao: FakeResenderDao) -> tuple:
    sender = FakeSender()
    interactor = AdminResendCurrentLevelInteractor(
        dao=dao,
        sender=sender,
        current_game=FakeCurrentGame(game=game),
    )
    return interactor, sender


@pytest.mark.asyncio
async def test_resends_the_puzzle_and_the_hints_already_released():
    """Exactly what the team should have on screen right now, no more."""
    game = make_game()
    team = make_team(1)
    dao = FakeResenderDao(
        teams=[team],
        level_times={team.id: level_time(5, team, game, number=0, minutes_ago=12)},
    )
    interactor, sender = build(game, dao)

    result = await interactor(identity=admin_identity(), team_id=team.id)

    assert result == [team]
    # 12 minutes in: the puzzle (0 min) and the 10-minute hint, not the 20-minute one
    assert sender.shown[0].view == [
        SendPuzzle(team=team, level=game.levels[0]),
        SendHint(team=team, hint_number=1, level=game.levels[0]),
    ]


@pytest.mark.asyncio
async def test_a_hint_whose_time_has_not_come_is_not_resent():
    game = make_game()
    team = make_team(1)
    dao = FakeResenderDao(
        teams=[team],
        level_times={team.id: level_time(5, team, game, number=1, minutes_ago=2)},
    )
    interactor, sender = build(game, dao)

    await interactor(identity=admin_identity(), team_id=team.id)

    assert sender.shown[0].view == [SendPuzzle(team=team, level=game.levels[1])]


@pytest.mark.asyncio
async def test_without_a_team_every_playing_team_gets_its_own_level():
    game = make_game()
    first, second = make_team(1), make_team(2)
    dao = FakeResenderDao(
        teams=[first, second],
        level_times={
            first.id: level_time(5, first, game, number=0, minutes_ago=1),
            second.id: level_time(6, second, game, number=1, minutes_ago=1),
        },
    )
    interactor, sender = build(game, dao)

    result = await interactor(identity=admin_identity())

    assert result == [first, second]
    assert sender.shown[0].view == [
        SendPuzzle(team=first, level=game.levels[0]),
        SendPuzzle(team=second, level=game.levels[1]),
    ]


@pytest.mark.asyncio
async def test_a_team_that_has_finished_is_answered_for_like_the_others():
    """The answer must not tell the admin who is through the last level."""
    game = make_game()
    playing, finished = make_team(1), make_team(2)
    dao = FakeResenderDao(
        teams=[playing, finished],
        level_times={
            playing.id: level_time(5, playing, game, number=0, minutes_ago=1),
            # level_number past the last level is what "finished" looks like
            finished.id: level_time(6, finished, game, number=2, minutes_ago=1),
        },
    )
    interactor, sender = build(game, dao)

    result = await interactor(identity=admin_identity())

    assert result == [playing, finished]
    assert sender.shown[0].view == [SendPuzzle(team=playing, level=game.levels[0])]


@pytest.mark.asyncio
async def test_a_team_without_a_level_time_costs_the_others_nothing():
    game = make_game()
    playing, stranger = make_team(1), make_team(2)
    dao = FakeResenderDao(
        teams=[playing, stranger],
        level_times={playing.id: level_time(5, playing, game, number=0, minutes_ago=1)},
    )
    interactor, sender = build(game, dao)

    result = await interactor(identity=admin_identity())

    assert result == [playing, stranger]
    assert sender.shown[0].view == [SendPuzzle(team=playing, level=game.levels[0])]


@pytest.mark.asyncio
async def test_a_team_that_does_not_play_is_refused():
    game = make_game()
    team = make_team(1)
    dao = FakeResenderDao(
        teams=[team],
        level_times={team.id: level_time(5, team, game, number=0, minutes_ago=1)},
    )
    interactor, sender = build(game, dao)

    with pytest.raises(exceptions.TeamError):
        await interactor(identity=admin_identity(), team_id=2)
    assert sender.shown == []


@pytest.mark.parametrize(
    "status", [GameStatus.getting_waivers, GameStatus.finished, GameStatus.complete]
)
@pytest.mark.asyncio
async def test_nothing_to_resend_until_the_game_runs(status: GameStatus):
    game = make_game(status)
    team = make_team(1)
    dao = FakeResenderDao(teams=[team])
    interactor, sender = build(game, dao)

    with pytest.raises(exceptions.GameStatusError):
        await interactor(identity=admin_identity())
    assert sender.shown == []


@pytest.mark.asyncio
async def test_a_player_who_is_not_an_admin_gets_nowhere():
    game = make_game()
    team = make_team(1)
    dao = FakeResenderDao(
        teams=[team],
        level_times={team.id: level_time(5, team, game, number=0, minutes_ago=1)},
    )
    interactor, sender = build(game, dao)
    player = dto.Player(id=2, can_be_author=False, is_dummy=False, username="player")

    with pytest.raises(exceptions.NotAuthorizedForAdmin):
        await interactor(identity=MockIdentityProvider(player=player))
    assert sender.shown == []
