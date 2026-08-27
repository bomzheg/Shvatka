import typing
from datetime import datetime
from uuid import uuid4

import pytest

from shvatka.core.games.interactors import CheckKeyInteractor
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import action
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.views.game import (
    DuplicateKey,
    EffectsKey,
    GameFinishedByAll,
    SendPuzzle,
    WrongKey,
    group_by_team,
)


def stub(name: str) -> typing.Any:
    """A stand-in for a dto the code under test only passes along."""
    return typing.cast(typing.Any, name)


def team(id_: int) -> dto.Team:
    return typing.cast(dto.Team, typing.cast(object, _Team(id_)))


class _Team:
    def __init__(self, id_: int) -> None:
        self.id = id_

    def __repr__(self) -> str:
        return f"team{self.id}"


def build_key(type_: enums.KeyType, *, is_duplicate: bool = False) -> dto.InsertedKey:
    effect = action.Effects(id=uuid4())
    return dto.InsertedKey(
        text="SHKEY",
        type_=type_,
        is_duplicate=is_duplicate,
        at=datetime.now(tz=tz_utc),
        level_number=0,
        player=stub("player"),
        team=team(1),
        level_up=False,
        parsed_key=dto.ParsedKey(text="SHKEY", type_=type_, effect=effect),
    )


def test_a_duplicate_is_only_told_it_is_a_duplicate() -> None:
    key = build_key(enums.KeyType.simple, is_duplicate=True)

    tasks = CheckKeyInteractor.view_(key, input_container="msg")

    # bonuses of a key already counted must not be announced a second time
    assert tasks == [DuplicateKey(key=key, input_container="msg")]


def test_a_wrong_key_is_told_it_is_wrong() -> None:
    key = build_key(enums.KeyType.wrong)

    assert CheckKeyInteractor.view_(key, input_container="msg") == [
        WrongKey(key=key, input_container="msg")
    ]


@pytest.mark.parametrize(
    "type_", [enums.KeyType.simple, enums.KeyType.bonus, enums.KeyType.effects]
)
def test_a_key_that_counted_carries_its_effects(type_: enums.KeyType) -> None:
    key = build_key(type_)

    tasks = CheckKeyInteractor.view_(key, input_container="msg")

    assert tasks == [EffectsKey(key=key, effects=key.parsed_key.effect, input_container="msg")]


def test_a_key_task_belongs_to_the_team_that_typed_it() -> None:
    key = build_key(enums.KeyType.wrong)

    assert WrongKey(key=key, input_container="msg").team is key.team


def test_one_team_is_shown_its_messages_in_order() -> None:
    one = team(1)
    tasks = [
        WrongKey(key=build_key(enums.KeyType.wrong), input_container="msg"),
        SendPuzzle(team=one, level=stub("level")),
    ]

    groups = group_by_team(tasks)

    # a key must be confirmed before the puzzle it opened
    assert groups == [tasks]


def test_teams_are_split_apart_so_they_can_be_shown_at_once() -> None:
    one, two, three = team(1), team(2), team(3)
    tasks = [
        GameFinishedByAll(team=one),
        GameFinishedByAll(team=two),
        GameFinishedByAll(team=three),
    ]

    groups = group_by_team(tasks)

    assert groups == [[tasks[0]], [tasks[1]], [tasks[2]]]


def test_a_teams_tasks_stay_together_even_when_interleaved() -> None:
    one, two = team(1), team(2)
    first_of_one = GameFinishedByAll(team=one)
    first_of_two = GameFinishedByAll(team=two)
    second_of_one = SendPuzzle(team=one, level=stub("level"))

    groups = group_by_team([first_of_one, first_of_two, second_of_one])

    assert groups == [[first_of_one, second_of_one], [first_of_two]]
