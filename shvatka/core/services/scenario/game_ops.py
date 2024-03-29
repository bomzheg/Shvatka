from dataclass_factory import Factory

from shvatka.core.models.dto import scn
from shvatka.core.services.scenario.level_ops import (
    check_all_files_saved as check_all_in_level_saved,
)


def parse_game(game: scn.RawGameScenario, dcf: Factory) -> scn.GameScenario:
    return dcf.load(game.scn, scn.GameScenario)


def parse_uploaded_game(game: scn.RawGameScenario, dcf: Factory) -> scn.UploadedGameScenario:
    return dcf.load(game.scn, scn.UploadedGameScenario)


def serialize(game: scn.FullGameScenario, dcf: Factory) -> dict:
    return dcf.dump(game)


def check_all_files_saved(game: scn.GameScenario, guids: set[str]):
    for level in game.levels:
        check_all_in_level_saved(level, guids)
