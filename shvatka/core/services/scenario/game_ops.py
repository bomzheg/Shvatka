from adaptix import Retort

from shvatka.core.models.dto import scn


def parse_game(game: scn.RawGameScenario, retort: Retort) -> scn.GameScenario:
    return retort.load(game.scn, scn.GameScenario)


def parse_uploaded_game(game: scn.RawGameScenario, retort: Retort) -> scn.UploadedGameScenario:
    return retort.load(game.scn, scn.UploadedGameScenario)


def serialize(game: scn.FullGameScenario, retort: Retort) -> dict:
    return retort.dump(game)
