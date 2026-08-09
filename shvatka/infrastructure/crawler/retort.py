from adaptix import NameStyle, Retort, name_mapping

from shvatka.common.factory import REQUIRED_GAME_RECIPES


def create_teams_retort() -> Retort:
    """Retort for the crawler's own ``teams.json``.

    Kebab-cased, because that is how the file is written — the parser that
    produces it and the loader that reads it back must agree.
    """
    return Retort(recipe=[name_mapping(name_style=NameStyle.LOWER_KEBAB)])


def create_scenario_retort() -> Retort:
    """Retort for the scenario zips the crawler builds out of forum games.

    Needs the game recipes, since a scenario carries ``HintsList`` and
    ``Conditions``, which are not models adaptix can walk on its own. The kebab
    name style is what the crawler has always written; it is applied after the
    game recipes so their explicit ``__model_version__`` mapping still wins.
    """
    return Retort(recipe=[*REQUIRED_GAME_RECIPES, name_mapping(name_style=NameStyle.LOWER_KEBAB)])
