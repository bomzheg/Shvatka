from datetime import timedelta

import pytest

from shvatka.core.models import dto


@pytest.fixture
def game_stat(
    finished_game: dto.FullGame, gryffindor: dto.Team, slytherin: dto.Team
) -> dto.GameStat:
    base_time = finished_game.start_at
    assert base_time
    return dto.GameStat(
        level_times={
            gryffindor: [
                dto.LevelTime(
                    id=1,
                    game=finished_game,
                    team=gryffindor,
                    level_number=1,
                    start_at=base_time,
                ),
                dto.LevelTime(
                    id=4,
                    game=finished_game,
                    team=gryffindor,
                    level_number=1,
                    start_at=base_time + timedelta(minutes=20),
                ),
                dto.LevelTime(
                    id=5,
                    game=finished_game,
                    team=gryffindor,
                    level_number=2,
                    start_at=base_time + timedelta(hours=30),
                ),
            ],
            slytherin: [
                dto.LevelTime(
                    id=2,
                    game=finished_game,
                    team=slytherin,
                    level_number=0,
                    start_at=base_time,
                ),
                dto.LevelTime(
                    id=3,
                    game=finished_game,
                    team=slytherin,
                    level_number=1,
                    start_at=base_time + timedelta(minutes=10),
                ),
                dto.LevelTime(
                    id=6,
                    game=finished_game,
                    team=slytherin,
                    level_number=2,
                    start_at=base_time + timedelta(minutes=40),
                ),
            ],
        }
    )
