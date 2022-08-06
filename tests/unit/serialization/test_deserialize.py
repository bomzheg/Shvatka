from dataclass_factory import Factory

from app.enums.hint_type import HintType
from app.services.scenario.game_ops import load_game


def test_deserialize_scn(simple_scn: dict, dcf: Factory):
    game = load_game(simple_scn, dcf)
    assert "My new game" == game.name
    assert HintType.text.name == game.levels[0].time_hints[0].hint[0].type
    assert "загадка" == game.levels[0].time_hints[0].hint[0].text
    assert HintType.gps.name == game.levels[0].time_hints[2].hint[0].type
