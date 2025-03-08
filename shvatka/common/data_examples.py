from datetime import datetime, timedelta

from shvatka.core.models import dto, enums
from shvatka.core.models.dto import scn
from shvatka.core.models.dto import hints

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
GAME_START_EXAMPLE = datetime.fromisoformat("2023-03-18 23:00:00Z")
game_example = dto.FullGame(
    id=10,
    author=author,
    name="Funny game",
    status=enums.GameStatus.complete,
    manage_token="",
    start_at=GAME_START_EXAMPLE,
    number=20,
    results=dto.GameResults(
        published_chanel_id=None,
        results_picture_file_id=None,
        keys_url=None,
    ),
    levels=[
        dto.Level(
            db_id=100,
            author=author,
            name_id="level_100",
            game_id=10,
            number_in_game=0,
            scenario=scn.LevelScenario.legacy_factory(
                id="level_100",
                keys={"SH1"},
                time_hints=scn.HintsList(
                    [
                        hints.TimeHint(
                            time=0,
                            hint=[
                                hints.TextHint(
                                    text="level_100_0",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=10,
                            hint=[
                                hints.TextHint(
                                    text="level_100_10",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=20,
                            hint=[
                                hints.TextHint(
                                    text="level_100_20",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=30,
                            hint=[
                                hints.TextHint(
                                    text="level_100_20",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=40,
                            hint=[
                                hints.TextHint(
                                    text="level_100_20",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=60,
                            hint=[
                                hints.TextHint(
                                    text="level_100_20",
                                ),
                            ],
                        ),
                    ]
                ),
            ),
        ),
        dto.Level(
            db_id=101,
            author=author,
            name_id="level_101",
            game_id=10,
            number_in_game=1,
            scenario=scn.LevelScenario.legacy_factory(
                id="level_101",
                keys={"SH2"},
                time_hints=scn.HintsList(
                    [
                        hints.TimeHint(
                            time=0,
                            hint=[
                                hints.TextHint(
                                    text="level_101_0",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=10,
                            hint=[
                                hints.TextHint(
                                    text="level_101_10",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=20,
                            hint=[
                                hints.TextHint(
                                    text="level_101_20",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=30,
                            hint=[
                                hints.TextHint(
                                    text="level_101_20",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=40,
                            hint=[
                                hints.TextHint(
                                    text="level_101_20",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=60,
                            hint=[
                                hints.TextHint(
                                    text="level_101_20",
                                ),
                            ],
                        ),
                    ]
                ),
            ),
        ),
        dto.Level(
            db_id=102,
            author=author,
            name_id="level_102",
            game_id=10,
            number_in_game=0,
            scenario=scn.LevelScenario.legacy_factory(
                id="level_102",
                keys={"SH3"},
                time_hints=scn.HintsList(
                    [
                        hints.TimeHint(
                            time=0,
                            hint=[
                                hints.TextHint(
                                    text="level_102_0",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=10,
                            hint=[
                                hints.TextHint(
                                    text="level_102_10",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=20,
                            hint=[
                                hints.TextHint(
                                    text="level_102_20",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=30,
                            hint=[
                                hints.TextHint(
                                    text="level_102_20",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=40,
                            hint=[
                                hints.TextHint(
                                    text="level_102_20",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=60,
                            hint=[
                                hints.TextHint(
                                    text="level_102_20",
                                ),
                            ],
                        ),
                    ]
                ),
            ),
        ),
        dto.Level(
            db_id=103,
            author=author,
            name_id="level_103",
            game_id=10,
            number_in_game=0,
            scenario=scn.LevelScenario.legacy_factory(
                id="level_103",
                keys={"SH4"},
                time_hints=scn.HintsList(
                    [
                        hints.TimeHint(
                            time=0,
                            hint=[
                                hints.TextHint(
                                    text="level_103_0",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=10,
                            hint=[
                                hints.TextHint(
                                    text="level_103_10",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=20,
                            hint=[
                                hints.TextHint(
                                    text="level_103_20",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=30,
                            hint=[
                                hints.TextHint(
                                    text="level_103_20",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=40,
                            hint=[
                                hints.TextHint(
                                    text="level_103_20",
                                ),
                            ],
                        ),
                        hints.TimeHint(
                            time=60,
                            hint=[
                                hints.TextHint(
                                    text="level_103_20",
                                ),
                            ],
                        ),
                    ]
                ),
            ),
        ),
    ],
)
game_stat_example = dto.GameStat(
    level_times={
        gryffindor: [
            dto.LevelTimeOnGame(
                id=1,
                game=game_example,
                team=gryffindor,
                level_number=0,
                start_at=GAME_START_EXAMPLE,
                is_finished=False,
                hint=dto.SpyHintInfo(number=0, time=0),
            ),
            dto.LevelTimeOnGame(
                id=2,
                game=game_example,
                team=gryffindor,
                level_number=0,
                start_at=GAME_START_EXAMPLE + timedelta(minutes=40),
                is_finished=False,
                hint=dto.SpyHintInfo(number=2, time=40),
            ),
            dto.LevelTimeOnGame(
                id=3,
                game=game_example,
                team=gryffindor,
                level_number=1,
                start_at=GAME_START_EXAMPLE + timedelta(minutes=60),
                is_finished=False,
                hint=dto.SpyHintInfo(number=1, time=20),
            ),
            dto.LevelTimeOnGame(
                id=4,
                game=game_example,
                team=gryffindor,
                level_number=2,
                start_at=GAME_START_EXAMPLE + timedelta(minutes=90),
                is_finished=False,
                hint=dto.SpyHintInfo(number=2, time=30),
            ),
            dto.LevelTimeOnGame(
                id=5,
                game=game_example,
                team=gryffindor,
                level_number=3,
                start_at=GAME_START_EXAMPLE + timedelta(minutes=120),
                is_finished=True,
                hint=dto.SpyHintInfo(number=2, time=30),
            ),
        ],
        slytherin: [
            dto.LevelTimeOnGame(
                id=5,
                game=game_example,
                team=slytherin,
                level_number=0,
                start_at=GAME_START_EXAMPLE,
                is_finished=False,
                hint=dto.SpyHintInfo(number=0, time=0),
            ),
            dto.LevelTimeOnGame(
                id=6,
                game=game_example,
                team=slytherin,
                level_number=0,
                start_at=GAME_START_EXAMPLE + timedelta(minutes=35),
                is_finished=False,
                hint=dto.SpyHintInfo(number=1, time=35),
            ),
            dto.LevelTimeOnGame(
                id=7,
                game=game_example,
                team=slytherin,
                level_number=1,
                start_at=GAME_START_EXAMPLE + timedelta(minutes=53),
                is_finished=False,
                hint=dto.SpyHintInfo(number=1, time=17),
            ),
            dto.LevelTimeOnGame(
                id=8,
                game=game_example,
                team=slytherin,
                level_number=2,
                start_at=GAME_START_EXAMPLE + timedelta(minutes=88),
                is_finished=False,
                hint=dto.SpyHintInfo(number=2, time=35),
            ),
            dto.LevelTimeOnGame(
                id=9,
                game=game_example,
                team=slytherin,
                level_number=3,
                start_at=GAME_START_EXAMPLE + timedelta(minutes=140),
                is_finished=True,
                hint=dto.SpyHintInfo(number=4, time=52),
            ),
        ],
    }
)
