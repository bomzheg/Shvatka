import typing

from shvatka.core.games.results import build_results_table
from shvatka.core.models import dto
from shvatka.infrastructure.printer.table import print_table


def export_results(game: dto.FullGame, game_stat: dto.GameStat, file: typing.Any) -> None:
    print_table(build_results_table(game, game_stat), file)
