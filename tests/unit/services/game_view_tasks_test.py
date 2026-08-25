"""Deciding what to show is a pure function over what the database said."""

import typing
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from shvatka.core.games.dto import LevelUpOutcome
from shvatka.core.games.interactors import key_tasks, level_up_tasks
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import action
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.views.game import (
    DuplicateKey,
    EffectsKey,
    GameFinished,
    GameFinishedByAll,
    GameLogType,
    LevelUp,
    SendPuzzle,
    WrongKey,
)


def stub(name: str):
    """A stand-in for a dto the code under test only passes along."""
    return typing.cast(typing.Any, name)


def build_key(type_: enums.KeyType, *, is_duplicate: bool = False) -> dto.InsertedKey:
    effect = action.Effects(id=uuid4())
    return dto.InsertedKey(
        text="SHKEY",
        type_=type_,
        is_duplicate=is_duplicate,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=stub("player"),
        team=stub("team"),
        level_up=False,
        parsed_key=dto.ParsedKey(text="SHKEY", type_=type_, effect=effect),
    )


def test_a_duplicate_is_only_told_it_is_a_duplicate() -> None:
    key = build_key(enums.KeyType.simple, is_duplicate=True)

    tasks = key_tasks(key, input_container="msg")

    # bonuses of a key already counted must not be announced a second time
    assert tasks == [DuplicateKey(key=key, input_container="msg")]


def test_a_wrong_key_is_told_it_is_wrong() -> None:
    key = build_key(enums.KeyType.wrong)

    assert key_tasks(key, input_container="msg") == [WrongKey(key=key, input_container="msg")]


@pytest.mark.parametrize(
    "type_", [enums.KeyType.simple, enums.KeyType.bonus, enums.KeyType.effects]
)
def test_a_key_that_counted_carries_its_effects(type_: enums.KeyType) -> None:
    key = build_key(type_)

    tasks = key_tasks(key, input_container="msg")

    assert tasks == [EffectsKey(key=key, effects=key.parsed_key.effect, input_container="msg")]


def test_a_level_up_shows_the_puzzle_and_tells_the_orgs() -> None:
    level = "next level"
    outcome = LevelUpOutcome(next_level=level, level_time_id=7, orgs=[stub("org")])

    tasks = level_up_tasks(outcome, input_container="msg", team="team", game="game")

    assert tasks.view == [SendPuzzle(team="team", level=level)]
    assert tasks.org == [LevelUp(team="team", new_level=level, orgs_list=[stub("org")])]
    assert tasks.log == [], "a level up is not news for the whole game"


def test_one_team_finishing_does_not_finish_the_game() -> None:
    outcome = LevelUpOutcome(team_finished=True)

    tasks = level_up_tasks(outcome, input_container="msg", team="team", game="game")

    assert tasks.view == [GameFinished(team="team", input_container="msg")]
    assert tasks.log == []
    assert tasks.org == []


def test_the_last_team_finishing_congratulates_everyone_and_logs_it() -> None:
    game = SimpleNamespace(name="ЗМ-1")
    outcome = LevelUpOutcome(
        team_finished=True, all_finished=True, finished_teams=[stub("one"), stub("two")]
    )

    tasks = level_up_tasks(outcome, input_container="msg", team="one", game=game)

    assert tasks.view == [
        GameFinished(team="one", input_container="msg"),
        GameFinishedByAll(team="one"),
        GameFinishedByAll(team="two"),
    ]
    assert len(tasks.log) == 1
    assert tasks.log[0].type == GameLogType.GAME_FINISHED
    assert tasks.log[0].data == {"game": "ЗМ-1"}
