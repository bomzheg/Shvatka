from datetime import datetime, timedelta

import pytest

from shvatka.core.models import dto


@pytest.fixture
def game_stat(finished_game: dto.FullGame, gryffindor: dto.Team, slytherin: dto.Team) -> dto.GameStat:
    base_time = finished_game.start_at
    return dto.GameStat(
        level_times={
            gryffindor: [
                dto.LevelTime(
                    id=1,
                    game=finished_game,
                    team=gryffindor,
                    level_number=0,
                    start_at=base_time + timedelta(minutes=20),
                ),
                dto.LevelTime(
                    id=1,
                    game=finished_game,
                    team=gryffindor,
                    level_number=1,
                    start_at=base_time + timedelta(hours=30),
                ),
            ],
            slytherin: [
                dto.LevelTime(
                    id=1,
                    game=finished_game,
                    team=slytherin,
                    level_number=0,
                    start_at=base_time + timedelta(minutes=10),
                ),
                dto.LevelTime(
                    id=1,
                    game=finished_game,
                    team=slytherin,
                    level_number=1,
                    start_at=base_time + timedelta(minutes=40),
                ),
            ],
        }
    )
