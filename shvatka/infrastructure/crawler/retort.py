from adaptix import NameStyle, Retort, name_mapping

from shvatka.common.factory import REQUIRED_GAME_RECIPES


def create_teams_retort() -> Retort:
    return Retort(recipe=[name_mapping(name_style=NameStyle.LOWER_KEBAB)])


def create_scenario_retort() -> Retort:
    return Retort(recipe=[*REQUIRED_GAME_RECIPES, name_mapping(name_style=NameStyle.LOWER_KEBAB)])
