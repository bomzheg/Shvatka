from copy import deepcopy

import pytest
from dataclass_factory import Factory

from shvatka.models.enums.hint_type import HintType
from shvatka.services.scenario.game_ops import load_game
from shvatka.services.scenario.level_ops import load_level
from shvatka.utils.exceptions import ScenarioNotCorrect


def test_deserialize_game(simple_scn: dict, dcf: Factory):
    game = load_game(simple_scn, dcf)
    assert "My new game" == game.name
    assert HintType.text.name == game.levels[0].time_hints[0].hint[0].type
    assert "загадка" == game.levels[0].time_hints[0].hint[0].text
    assert HintType.gps.name == game.levels[0].time_hints[2].hint[0].type


def test_deserialize_level(simple_scn: dict, dcf: Factory):
    level = load_level(simple_scn["levels"][0], dcf)
    assert "first" == level.id
    assert HintType.text.name == level.time_hints[0].hint[0].type
    assert "загадка" == level.time_hints[0].hint[0].text
    assert HintType.gps.name == level.time_hints[2].hint[0].type


def test_deserialize_invalid_level(simple_scn: dict, dcf: Factory):
    level_source = simple_scn["levels"][0]
    level = deepcopy(level_source)
    level["id"] = "привет"
    with pytest.raises(ScenarioNotCorrect):
        load_level(level, dcf)

    level["keys"] = {"SHCamelCase"}
    with pytest.raises(ScenarioNotCorrect):
        load_level(level, dcf)

    level = deepcopy(level_source)
    level["time_hints"] = level.pop("time-hints")
    with pytest.raises(ScenarioNotCorrect):
        load_level(level, dcf)
