from datetime import datetime, timedelta
from itertools import pairwise
from typing import NamedTuple

import matplotlib.pyplot as plt

from shvatka.core.models import dto, enums
from shvatka.core.models.dto import scn


class PlotData(NamedTuple):
    abscissa: list[datetime]
    ordinate: list[float]


def paint_it(stat: dto.GameStat, game: dto.FullGame):
    converted = convert(stat, game)
    fig, ax = plt.subplots()
    for team, data in converted.items():
        plt.plot(*data, label=team)
    ax.legend()
    plt.grid()
    plt.ylim([0, len(game.levels)])
    plt.xlim(game.start_at, max([x for plotdata in converted.values() for x in plotdata.abscissa]) + timedelta(minutes=10))
    plt.show()


def convert(stat: dto.GameStat, game: dto.FullGame) -> dict[str, PlotData]:
    result = {}
    for team, level_times in stat.level_times.items():
        abscissa: list[datetime] = []
        ordinate: list[float] = []
        current_ordinate = 0.0
        for level_time_prev, level_time_now in pairwise([None, *level_times]):  # type: dto.LevelTimeOnGame | None, dto.LevelTimeOnGame
            if level_time_prev is None:
                abscissa.append(game.start_at)
                current_ordinate = level_time_now.level_number
                ordinate.append(current_ordinate)
                continue
            minutes_to_level = (level_time_now.start_at - level_time_prev.start_at).seconds / 60
            this_level_scn = game.levels[level_time_prev.level_number].scenario
            step_per_hint = 0.6 / len(this_level_scn.time_hints)
            for hint in this_level_scn.time_hints[1:]:
                if hint.time > minutes_to_level:
                    break
                add_next(abscissa, ordinate, current_ordinate, level_time_prev.start_at + timedelta(minutes=hint.time), current_ordinate + step_per_hint)
                current_ordinate += step_per_hint

            add_next(abscissa, ordinate, current_ordinate, level_time_now.start_at, level_time_now.level_number + 1)
            current_ordinate = level_time_now.level_number + 1
        result[team.name] = PlotData(abscissa, ordinate)
    return result


def add_next(abscissa: list[datetime], ordinate: list[float], before: float, at: datetime, after: float):
    abscissa.append(at - timedelta(seconds=1))
    ordinate.append(before)
    abscissa.append(at)
    ordinate.append(after)


if __name__ == '__main__':
    gryffindor = dto.Team(
        id=1,
        name="Gryffindor",
        captain=None,
        description=None,
        is_dummy=False,
    )
    slytherin = dto.Team(
        id=2,
        name="Slytherin",
        captain=None,
        description=None,
        is_dummy=False,
    )
    author = dto.Player(id=100, can_be_author=True, is_dummy=False)
    test_game = dto.FullGame(
        id=10,
        author=author,
        name="happy game",
        status=enums.GameStatus.complete,
        manage_token="",
        start_at=datetime.fromisoformat("2023-03-18 23:00:00Z"),
        number=20,
        published_channel_id=None,
        levels=[
            dto.Level(
                db_id=100,
                author=author,
                name_id="level_100",
                game_id=10,
                number_in_game=0,
                scenario=scn.LevelScenario(
                    id="level_100",
                    keys={"SH1"},
                    time_hints=[
                        scn.TimeHint(
                            time=0,
                            hint=[
                                scn.TextHint(
                                    text="level_100_0",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=10,
                            hint=[
                                scn.TextHint(
                                    text="level_100_10",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=20,
                            hint=[
                                scn.TextHint(
                                    text="level_100_20",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=30,
                            hint=[
                                scn.TextHint(
                                    text="level_100_20",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=40,
                            hint=[
                                scn.TextHint(
                                    text="level_100_20",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=60,
                            hint=[
                                scn.TextHint(
                                    text="level_100_20",
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            dto.Level(
                db_id=101,
                author=author,
                name_id="level_101",
                game_id=10,
                number_in_game=1,
                scenario=scn.LevelScenario(
                    id="level_101",
                    keys={"SH2"},
                    time_hints=[
                        scn.TimeHint(
                            time=0,
                            hint=[
                                scn.TextHint(
                                    text="level_101_0",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=10,
                            hint=[
                                scn.TextHint(
                                    text="level_101_10",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=20,
                            hint=[
                                scn.TextHint(
                                    text="level_101_20",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=30,
                            hint=[
                                scn.TextHint(
                                    text="level_101_20",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=40,
                            hint=[
                                scn.TextHint(
                                    text="level_101_20",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=60,
                            hint=[
                                scn.TextHint(
                                    text="level_101_20",
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            dto.Level(
                db_id=102,
                author=author,
                name_id="level_102",
                game_id=10,
                number_in_game=0,
                scenario=scn.LevelScenario(
                    id="level_102",
                    keys={"SH3"},
                    time_hints=[
                        scn.TimeHint(
                            time=0,
                            hint=[
                                scn.TextHint(
                                    text="level_102_0",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=10,
                            hint=[
                                scn.TextHint(
                                    text="level_102_10",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=20,
                            hint=[
                                scn.TextHint(
                                    text="level_102_20",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=30,
                            hint=[
                                scn.TextHint(
                                    text="level_102_20",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=40,
                            hint=[
                                scn.TextHint(
                                    text="level_102_20",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=60,
                            hint=[
                                scn.TextHint(
                                    text="level_102_20",
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            dto.Level(
                db_id=103,
                author=author,
                name_id="level_103",
                game_id=10,
                number_in_game=0,
                scenario=scn.LevelScenario(
                    id="level_103",
                    keys={"SH4"},
                    time_hints=[
                        scn.TimeHint(
                            time=0,
                            hint=[
                                scn.TextHint(
                                    text="level_103_0",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=10,
                            hint=[
                                scn.TextHint(
                                    text="level_103_10",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=20,
                            hint=[
                                scn.TextHint(
                                    text="level_103_20",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=30,
                            hint=[
                                scn.TextHint(
                                    text="level_103_20",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=40,
                            hint=[
                                scn.TextHint(
                                    text="level_103_20",
                                ),
                            ],
                        ),
                        scn.TimeHint(
                            time=60,
                            hint=[
                                scn.TextHint(
                                    text="level_103_20",
                                ),
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )
    test_data = dto.GameStat(
        level_times={
            gryffindor: [
                dto.LevelTimeOnGame(id=1, game=test_game, team=gryffindor, level_number=0, start_at=test_game.start_at, is_finished=False,),
                dto.LevelTimeOnGame(id=2, game=test_game, team=gryffindor, level_number=0, start_at=test_game.start_at + timedelta(minutes=40), is_finished=False,),
                dto.LevelTimeOnGame(id=3, game=test_game, team=gryffindor, level_number=1, start_at=test_game.start_at + timedelta(minutes=60), is_finished=False,),
                dto.LevelTimeOnGame(id=4, game=test_game, team=gryffindor, level_number=2, start_at=test_game.start_at + timedelta(minutes=90), is_finished=False,),
                dto.LevelTimeOnGame(id=5, game=test_game, team=gryffindor, level_number=3, start_at=test_game.start_at + timedelta(minutes=120), is_finished=True,),
            ],
            slytherin: [
                dto.LevelTimeOnGame(id=5, game=test_game, team=slytherin, level_number=0, start_at=test_game.start_at, is_finished=False,),
                dto.LevelTimeOnGame(id=6, game=test_game, team=slytherin, level_number=0, start_at=test_game.start_at + timedelta(minutes=35), is_finished=False,),
                dto.LevelTimeOnGame(id=7, game=test_game, team=slytherin, level_number=1, start_at=test_game.start_at + timedelta(minutes=53), is_finished=False,),
                dto.LevelTimeOnGame(id=8, game=test_game, team=slytherin, level_number=2, start_at=test_game.start_at + timedelta(minutes=88), is_finished=False,),
                dto.LevelTimeOnGame(id=9, game=test_game, team=slytherin, level_number=3, start_at=test_game.start_at + timedelta(minutes=140), is_finished=True,),
            ],
        }
    )
    paint_it(test_data, test_game)
