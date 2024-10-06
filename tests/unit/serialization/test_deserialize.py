from copy import deepcopy

import pytest
from adaptix import Retort

from shvatka.core.models.dto.scn import TextHint, GPSHint, PhotoHint, ContactHint
from shvatka.core.models.dto.scn.game import RawGameScenario
from shvatka.core.models.dto.scn.hint_part import (
    VenueHint,
    AudioHint,
    VideoHint,
    DocumentHint,
    AnimationHint,
    VoiceHint,
    VideoNoteHint,
    StickerHint,
)
from shvatka.core.models.enums import HintType
from shvatka.core.services.level import load_level
from shvatka.core.services.scenario.game_ops import parse_game
from shvatka.core.utils.exceptions import ScenarioNotCorrect
from shvatka.tgbot.views.utils import render_hints


def test_deserialize_game(simple_scn: RawGameScenario, retort: Retort):
    game = parse_game(simple_scn, retort)
    assert "My new game" == game.name
    assert HintType.text.name == game.levels[0].time_hints[0].hint[0].type
    assert "загадка" == game.levels[0].time_hints[0].hint[0].text
    assert HintType.gps.name == game.levels[0].time_hints[2].hint[0].type


def test_deserialize_level(simple_scn: RawGameScenario, retort: Retort):
    level = load_level(simple_scn.scn["levels"][0], retort)
    assert "first" == level.id
    assert HintType.text.name == level.time_hints[0].hint[0].type
    assert "загадка" == level.time_hints[0].hint[0].text
    assert HintType.gps.name == level.time_hints[2].hint[0].type


def test_deserialize_invalid_level(simple_scn: RawGameScenario, retort: Retort):
    level_source = simple_scn.scn["levels"][0]
    level = deepcopy(level_source)
    level["id"] = "привет"
    with pytest.raises(ScenarioNotCorrect):
        load_level(level, retort)

    level["keys"] = {"SHCamelCase"}
    with pytest.raises(ScenarioNotCorrect):
        load_level(level, retort)

    level = deepcopy(level_source)
    level["time_hints"] = level.pop("time-hints")
    with pytest.raises(ScenarioNotCorrect):
        load_level(level, retort)


def test_deserialize_all_types(all_types_scn: RawGameScenario, retort: Retort):
    game_scn = parse_game(all_types_scn, retort)
    hints = game_scn.levels[0].time_hints
    assert 12 == len(hints)
    for i, type_ in enumerate(
        [
            TextHint,
            GPSHint,
            VenueHint,
            PhotoHint,
            AudioHint,
            VideoHint,
            DocumentHint,
            AnimationHint,
            VoiceHint,
            VideoNoteHint,
            ContactHint,
            StickerHint,
        ]
    ):
        assert isinstance(hints[i].hint[0], type_)
        assert hints[i].hint[0].type == type_.type  # type: ignore[attr-defined]


def test_render_all_types(all_types_scn: RawGameScenario, retort: Retort):
    game_scn = parse_game(all_types_scn, retort)
    hints = [time_hint.hint[0] for time_hint in game_scn.levels[0].time_hints]
    assert 12 == len(hints)
    assert "📃📡🧭📷🎼🎬📎🌀🎤🤳🪪🏷" == render_hints(hints)
