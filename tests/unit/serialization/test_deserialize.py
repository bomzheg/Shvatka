from copy import deepcopy

import pytest
from adaptix import Retort

from shvatka.common.data_examples import game_example, GAME_START_EXAMPLE
from shvatka.core.models.dto.hints import TextHint, GPSHint, PhotoHint, ContactHint
from shvatka.core.models.dto.scn import RawGameScenario
from shvatka.core.models.dto.hints import (
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
from shvatka.core.services.scenario.game_ops import parse_game, parse_uploaded_game
from shvatka.core.utils import exceptions
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


def test_deserialize_bonus_hint_without_correct_guid(
    no_file_guid_scn: RawGameScenario, retort: Retort
):
    with pytest.raises(exceptions.FileNotFound):
        parse_uploaded_game(no_file_guid_scn, retort)


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


def test_serialize_simple(retort: Retort):
    serialized = retort.dump(game_example)
    assert serialized == {
        "name": "Funny game",
        "author": {"can-be-author": True, "id": 100, "is-dummy": False},
        "id": 10,
        "number": 20,
        "manage-token": "",
        "start-at": GAME_START_EXAMPLE.isoformat(),
        "status": "complete",
        "results": {
            "published-chanel-id": None,
            "results-picture-file-id": None,
            "keys-url": None,
        },
        "levels": [
            {
                "db-id": 100,
                "author": {"can-be-author": True, "id": 100, "is-dummy": False},
                "name-id": "level_100",
                "game-id": 10,
                "number-in-game": 0,
                "scenario": {
                    "id": "level_100",
                    "__model_version__": 1,
                    "conditions": [
                        {
                            "type": "WIN_KEY",
                            "next-level": None,
                            "keys": ("SH1",),
                        }
                    ],
                    "time-hints": [
                        {
                            "time": 0,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_100_0",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 10,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_100_10",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 20,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_100_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 30,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_100_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 40,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_100_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 60,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_100_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                    ],
                },
            },
            {
                "db-id": 101,
                "author": {"can-be-author": True, "id": 100, "is-dummy": False},
                "name-id": "level_101",
                "game-id": 10,
                "number-in-game": 1,
                "scenario": {
                    "id": "level_101",
                    "__model_version__": 1,
                    "conditions": [
                        {
                            "type": "WIN_KEY",
                            "next-level": None,
                            "keys": ("SH2",),
                        }
                    ],
                    "time-hints": [
                        {
                            "time": 0,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_101_0",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 10,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_101_10",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 20,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_101_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 30,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_101_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 40,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_101_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 60,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_101_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                    ],
                },
            },
            {
                "db-id": 102,
                "author": {"can-be-author": True, "id": 100, "is-dummy": False},
                "name-id": "level_102",
                "game-id": 10,
                "number-in-game": 0,
                "scenario": {
                    "id": "level_102",
                    "__model_version__": 1,
                    "conditions": [
                        {
                            "type": "WIN_KEY",
                            "next-level": None,
                            "keys": ("SH3",),
                        }
                    ],
                    "time-hints": [
                        {
                            "time": 0,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_102_0",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 10,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_102_10",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 20,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_102_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 30,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_102_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 40,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_102_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 60,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_102_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                    ],
                },
            },
            {
                "db-id": 103,
                "author": {"can-be-author": True, "id": 100, "is-dummy": False},
                "name-id": "level_103",
                "game-id": 10,
                "number-in-game": 0,
                "scenario": {
                    "id": "level_103",
                    "__model_version__": 1,
                    "conditions": [
                        {
                            "type": "WIN_KEY",
                            "next-level": None,
                            "keys": ("SH4",),
                        }
                    ],
                    "time-hints": [
                        {
                            "time": 0,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_103_0",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 10,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_103_10",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 20,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_103_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 30,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_103_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 40,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_103_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                        {
                            "time": 60,
                            "hint": [
                                {
                                    "type": "text",
                                    "text": "level_103_20",
                                    "link-preview": None,
                                }
                            ],
                        },
                    ],
                },
            },
        ],
    }
