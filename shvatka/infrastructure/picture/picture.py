import logging
import pprint
from datetime import datetime, timedelta
from io import BytesIO
from itertools import pairwise
from typing import NamedTuple, BinaryIO

import matplotlib.dates as mdates
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator

from shvatka.common.data_examples import game_stat_example, game_example
from shvatka.core.models import dto
from shvatka.core.utils.datetime_utils import tz_game

logger = logging.getLogger(__name__)


class PlotData(NamedTuple):
    abscissa: list[datetime]
    ordinate: list[float]


def paint_it(stat: dto.GameStat, game: dto.FullGame) -> BinaryIO:
    converted = convert(stat, game)
    logger.debug("converted \n%s\nto\n%s\n", pprint.pformat(stat), pprint.pformat(converted))
    plot_it(converted, game)
    result = BytesIO()
    plt.savefig(result, format="png")
    plt.close()
    result.seek(0)
    return result


def plot_it(converted: dict[str, PlotData], game: dto.FullGame):
    fig, ax = plt.subplots()
    for team, data in converted.items():
        plt.plot(*data, label=team)  # type: ignore[arg-type]
    ax.legend()
    plt.grid()
    plt.ylim([1, len(game.levels) + 1])
    plt.xlim(
        game.start_at,
        max([x for plotdata in converted.values() for x in plotdata.abscissa])
        + timedelta(minutes=5),
    )
    plt.xticks(rotation="vertical")
    ax.yaxis.set_major_locator(MultipleLocator(1))
    ax.set_ylabel("Уровень")
    ax.set_xlabel("Время")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=tz_game))
    ax.set_title(game.name)


def convert(stat: dto.GameStat, game: dto.FullGame) -> dict[str, PlotData]:
    result = {}
    for team, level_times in stat.level_times.items():
        abscissa: list[datetime] = []
        ordinate: list[float] = []
        current_ordinate = 1.0
        for level_time_prev, level_time_now in pairwise([None, *level_times]):  # type: dto.LevelTimeOnGame | None, dto.LevelTimeOnGame | None
            assert level_time_now is not None
            if level_time_prev is None:
                assert game.start_at
                abscissa.append(game.start_at)
                current_ordinate = level_time_now.level_number + 1
                ordinate.append(current_ordinate)
                continue
            minutes_to_level = (level_time_now.start_at - level_time_prev.start_at).seconds / 60
            this_level_scn = game.levels[level_time_prev.level_number].scenario
            step_per_hint = 0.6 / len(this_level_scn.time_hints)
            for hint in this_level_scn.time_hints[1:]:
                if hint.time > minutes_to_level:
                    break
                add_next(
                    abscissa,
                    ordinate,
                    current_ordinate,
                    level_time_prev.start_at + timedelta(minutes=hint.time),
                    current_ordinate + step_per_hint,
                )
                current_ordinate += step_per_hint

            add_next(
                abscissa,
                ordinate,
                current_ordinate,
                level_time_now.start_at,
                level_time_now.level_number + 1 + 1,
            )
            current_ordinate = level_time_now.level_number + 1 + 1
        result[team.name] = PlotData(abscissa, ordinate)
    return result


def add_next(
    abscissa: list[datetime], ordinate: list[float], before: float, at: datetime, after: float
):
    abscissa.append(at - timedelta(seconds=1))
    ordinate.append(before)
    abscissa.append(at)
    ordinate.append(after)


if __name__ == "__main__":
    plot_it(convert(game_stat_example, game_example), game_example)
    plt.show()
