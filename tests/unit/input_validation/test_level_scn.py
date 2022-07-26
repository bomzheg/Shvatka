import typing

import pytest
import ujson as json
from aiogram import types

from app.models.dto import LevelScenario, TimeHint, BaseHint
from app.utils.exceptions import ScenarioNotCorrect

USER_ID = 1


@pytest.mark.skip
def test_create_text_level():
    text_kwargs = dict(text='some')

    lvl = create_simple_lvl(USER_ID, types.Message(**text_kwargs))

    assert isinstance(lvl, LevelScenario)
    assert text_kwargs == lvl.time_hints[0].hint[0].kwargs

    json_cont = json.dumps(lvl.get_json_serializable())
    lvl2 = LevelScenario.parse_as_level(json.loads(json_cont))
    assert isinstance(lvl2, LevelScenario)
    assert lvl2.time_hints[0].hint[0].kwargs == lvl.time_hints[0].hint[0].kwargs


@pytest.mark.skip
def test_create_photo_level():
    photo_kwargs = dict(photo=[{"file_id": 5}])
    lvl = create_simple_lvl(USER_ID, types.Message(**photo_kwargs))
    hint_ = lvl.time_hints[0].hint[0]
    assert hint_.kwargs | next(hint_.file_kwargs()) == {'caption': None, 'photo': 5}

    json_cont = json.dumps(lvl.get_json_serializable())
    lvl2 = LevelScenario.parse_as_level(json.loads(json_cont))
    assert isinstance(lvl2, LevelScenario)
    assert hint_.kwargs == lvl2.time_hints[0].hint[0].kwargs


@pytest.mark.skip
def test_create_photo_caption_level():
    photo_kwargs = dict(photo=[{"file_id": 6}], caption="123")
    lvl = create_simple_lvl(USER_ID, types.Message(**photo_kwargs))
    hint_ = lvl.time_hints[0].hint[0]
    assert hint_.kwargs | next(hint_.file_kwargs()) == {'caption': "123", 'photo': 6}

    json_cont = json.dumps(lvl.get_json_serializable())
    lvl2 = LevelScenario.parse_as_level(json.loads(json_cont))
    assert isinstance(lvl2, LevelScenario)
    assert lvl2.time_hints[0].hint[0].kwargs == hint_.kwargs


@pytest.mark.skip
def test_create_photo_error_level():
    photo_kwargs = dict(photo=[{}], caption="123")
    with pytest.raises(ScenarioNotCorrect):
        create_simple_lvl(USER_ID, types.Message(**photo_kwargs))


def create_simple_lvl(
    user_id,
    msg: types.Message,
    lvl_id: str = "test_1",
    keys: typing.Iterable[str] = ("СХ123", "SH123")
):
    return LevelScenario(
        user_id,
        lvl_id,
        set(keys),
        [
            TimeHint(
                0, [BaseHint.save_content(msg)]
            )
        ]
    )
