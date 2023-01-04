from dataclass_factory import Factory

from shvatka.models.dto.scn import GameScenario, FullGameScenario
from shvatka.models.dto.scn.game import UploadedGameScenario
from shvatka.services.scenario.level_ops import check_all_files_saved as check_all_in_level_saved


def parse_game(scenario: dict, dcf: Factory) -> GameScenario:
    return dcf.load(scenario, GameScenario)


def parse_uploaded_game(scenario: dict, dcf: Factory) -> UploadedGameScenario:
    return dcf.load(scenario, UploadedGameScenario)


def serialize(game: FullGameScenario, dcf: Factory) -> dict:
    return dcf.dump(game)


def check_all_files_saved(game: GameScenario, guids: set[str]):
    for level in game.levels:
        check_all_in_level_saved(level, guids)
