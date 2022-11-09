from dataclass_factory import Factory

from shvatka.models.dto.scn import GameScenario, CompleteGameScenario
from shvatka.services.scenario.level_ops import check_all_files_saved as check_all_in_level_saved


def parse_game(scn: dict, dcf: Factory) -> GameScenario:
    return dcf.load(scn, GameScenario)


def parse_uploaded_game(scn: dict, dcf: Factory) -> CompleteGameScenario:
    return dcf.load(scn, CompleteGameScenario)


def serialize(game: CompleteGameScenario, dcf: Factory) -> dict:
    return dcf.dump(game)


def check_all_files_saved(game: GameScenario, guids: set[str]):
    for level in game.levels:
        check_all_in_level_saved(level, guids)
