from adaptix import Retort

from shvatka.core.models.dto import scn
from shvatka.core.services.scenario.level_ops import (
    check_all_files_saved as check_all_in_level_saved,
)


def parse_game(game: scn.RawGameScenario, retort: Retort) -> scn.GameScenario:
    return retort.load(game.scn, scn.GameScenario)


def parse_uploaded_game(game: scn.RawGameScenario, retort: Retort) -> scn.UploadedGameScenario:
    return retort.load(game.scn, scn.UploadedGameScenario)


def serialize(game: scn.FullGameScenario, retort: Retort) -> dict:
    return retort.dump(game)


def check_all_files_saved(game: scn.GameScenario, guids: set[str]):
    for level in game.levels:
        check_all_in_level_saved(level, guids)
