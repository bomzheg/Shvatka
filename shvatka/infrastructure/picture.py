from datetime import datetime, timedelta
from typing import NamedTuple

import matplotlib.pyplot as plt

from shvatka.core.models import dto, enums


class PlotData(NamedTuple):
    abscissa: list[datetime]
    ordinate: list[float]


def paint_it(stat: dto.GameStat):
    converted = convert(stat)
    fig, ax = plt.subplots()
    for team, data in converted.items():
        plt.plot(*data, label=team)
    plt.show()


def convert(stat: dto.GameStat) -> dict[str, PlotData]:
    result = {}
    for team, level_times in stat.level_times.items():
        abscissa, ordinate = [], []
        for level_time in level_times:
            abscissa.append(level_time.start_at - timedelta(seconds=1))
            ordinate.append(level_time.level_number - 1)
            abscissa.append(level_time.start_at)
            ordinate.append(level_time.level_number)
        result[team.name] = PlotData(abscissa[1:], ordinate[1:])
    return result


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
    test_game = dto.Game(
        id=10,
        author=dto.Player(id=100, can_be_author=True, is_dummy=False),
        name="happy game",
        status=enums.GameStatus.complete,
        manage_token="",
        start_at=datetime.utcnow() - timedelta(hours=12),
        number=20,
        published_channel_id=None,
    )
    test_data = dto.GameStat(
        level_times={
            gryffindor: [
                dto.LevelTimeOnGame(id=1, game=test_game, team=gryffindor, level_number=0, start_at=test_game.start_at + timedelta(minutes=40), is_finished=False,),
                dto.LevelTimeOnGame(id=2, game=test_game, team=gryffindor, level_number=1, start_at=test_game.start_at + timedelta(minutes=60), is_finished=False,),
                dto.LevelTimeOnGame(id=3, game=test_game, team=gryffindor, level_number=2, start_at=test_game.start_at + timedelta(minutes=90), is_finished=False,),
                dto.LevelTimeOnGame(id=4, game=test_game, team=gryffindor, level_number=3, start_at=test_game.start_at + timedelta(minutes=120), is_finished=True,),
            ],
            slytherin: [
                dto.LevelTimeOnGame(id=5, game=test_game, team=slytherin, level_number=0, start_at=test_game.start_at + timedelta(minutes=30), is_finished=False,),
                dto.LevelTimeOnGame(id=6, game=test_game, team=slytherin, level_number=1, start_at=test_game.start_at + timedelta(minutes=50), is_finished=False,),
                dto.LevelTimeOnGame(id=7, game=test_game, team=slytherin, level_number=2, start_at=test_game.start_at + timedelta(minutes=80), is_finished=False,),
                dto.LevelTimeOnGame(id=8, game=test_game, team=slytherin, level_number=3, start_at=test_game.start_at + timedelta(minutes=140), is_finished=True,),
            ],
        }
    )
    paint_it(test_data)
