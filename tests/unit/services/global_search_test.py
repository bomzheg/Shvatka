import uuid

from shvatka.core.models import dto
from shvatka.core.models.dto import action, hints, scn
from shvatka.core.models.enums import GameStatus
from shvatka.core.search.dto import LevelMatchField, LevelWithGame, PlayerMatchField
from shvatka.core.search.interactors import (
    classify_player_hit,
    find_level_hits,
    iter_hint_texts,
    make_snippet,
)


def test_make_snippet_found_case_insensitive():
    assert make_snippet("Съешь ещё этих мягких булок", "БУЛОК") == "Съешь ещё этих мягких булок"


def test_make_snippet_not_found():
    assert make_snippet("совсем другой текст", "булок") is None


def test_make_snippet_cuts_long_text():
    text = "а" * 100 + "иголка" + "б" * 100
    snippet = make_snippet(text, "иголка", radius=10)
    assert snippet == "…" + "а" * 10 + "иголка" + "б" * 10 + "…"


def test_iter_hint_texts():
    assert list(iter_hint_texts(hints.TextHint(text="загадка"))) == ["загадка"]
    assert list(
        iter_hint_texts(hints.PhotoHint(file_guid=str(uuid.uuid4()), caption="подпись"))
    ) == ["подпись"]
    assert list(iter_hint_texts(hints.PhotoHint(file_guid=str(uuid.uuid4())))) == []
    assert list(
        iter_hint_texts(
            hints.VenueHint(latitude=1.0, longitude=1.0, title="кафе", address="улица")
        )
    ) == ["кафе", "улица"]
    assert list(iter_hint_texts(hints.GPSHint(latitude=1.0, longitude=1.0))) == []


def _make_author() -> dto.Player:
    return dto.Player(id=1, can_be_author=True, is_dummy=False, username="author")


def _make_game(author: dto.Player) -> dto.Game:
    return dto.Game(
        id=10,
        author=author,
        name="Ночной дозор",
        status=GameStatus.complete,
        manage_token="",
        start_at=None,
        number=5,
        results=dto.GameResults(
            published_chanel_id=None,
            results_picture_file_id=None,
            keys_url=None,
        ),
    )


def _make_candidate() -> LevelWithGame:
    author = _make_author()
    scenario = scn.LevelScenario(
        id="arena",
        time_hints=scn.HintsList(
            [
                hints.TimeHint(time=0, hint=[hints.TextHint(text="загадка про arena")]),
                hints.TimeHint(
                    time=5,
                    hint=[
                        hints.TextHint(text="ничего интересного"),
                        hints.PhotoHint(file_guid=str(uuid.uuid4()), caption="это Arena цирка"),
                    ],
                ),
            ]
        ),
        conditions=scn.Conditions([action.KeyWinCondition({"SH123"})]),
        __model_version__=1,
    )
    level = dto.Level(
        db_id=100,
        name_id="arena",
        author=author,
        scenario=scenario,
        game_id=10,
        number_in_game=2,
    )
    return LevelWithGame(level=level, game=_make_game(author))


def test_find_level_hits_in_name_id_and_hints():
    candidate = _make_candidate()
    hits_found = find_level_hits(candidate, "arena")
    assert len(hits_found) == 3

    name_id_hit = hits_found[0]
    assert name_id_hit.found_in == LevelMatchField.name_id
    assert name_id_hit.snippet == "arena"
    assert name_id_hit.hint_number is None

    first_hint_hit = hits_found[1]
    assert first_hint_hit.found_in == LevelMatchField.hint
    assert first_hint_hit.hint_number == 0
    assert first_hint_hit.hint_time == 0
    assert first_hint_hit.hint_part_number == 0
    assert first_hint_hit.snippet == "загадка про arena"

    caption_hit = hits_found[2]
    assert caption_hit.hint_number == 1
    assert caption_hit.hint_time == 5
    assert caption_hit.hint_part_number == 1
    assert caption_hit.snippet == "это Arena цирка"


def test_find_level_hits_nothing():
    candidate = _make_candidate()
    assert find_level_hits(candidate, "иголка") == []


def test_classify_player_hit_priority():
    player = dto.Player(
        id=2,
        can_be_author=False,
        is_dummy=False,
        username="harry",
        user=dto.User(tg_id=666, username="harry_tg", first_name="Harry", last_name="Potter"),
        forum_user=dto.ForumUser(
            db_id=3, forum_id=3, name="HarryForum", registered=None, player_id=2
        ),
    )
    hit = classify_player_hit(player, "harry")
    assert hit is not None
    assert hit.found_in == PlayerMatchField.username

    hit = classify_player_hit(player, "harry_tg")
    assert hit is not None
    assert hit.found_in == PlayerMatchField.tg_username

    hit = classify_player_hit(player, "Potter")
    assert hit is not None
    assert hit.found_in == PlayerMatchField.tg_name
    assert hit.snippet == "Harry Potter"

    hit = classify_player_hit(player, "HarryForum")
    assert hit is not None
    assert hit.found_in == PlayerMatchField.forum_name

    assert classify_player_hit(player, "hermione") is None


def test_get_tg_fullname():
    player = dto.Player(
        id=2,
        can_be_author=False,
        is_dummy=False,
        user=dto.User(tg_id=666, first_name="Harry", last_name="Potter"),
    )
    assert player.get_tg_fullname() == "Harry Potter"
    assert _make_author().get_tg_fullname() is None
