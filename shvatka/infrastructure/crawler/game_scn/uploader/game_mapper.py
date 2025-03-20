from typing import TypeVar, Sequence

from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.infrastructure.crawler.models import uploadable_game as data


def map_game_for_upload(game: dto.FullGame) -> data.GameForUpload:
    return [map_level_for_upload(level) for level in game.levels]


def map_level_for_upload(level: dto.Level) -> data.LevelForUpload:
    assert level.number_in_game is not None
    scn = level.scenario
    first_hint = scn.time_hints[0]
    puzzle = data.LevelPuzzle(
        level_number=level.number_in_game + 1,
        hint_number=0,
        next_hint_time=scn.time_hints[1].time,
        text=hint_parts_to_text(first_hint.hint),
        key="".join(scn.get_keys()),
        brain_key="",
    )
    hints_ = []
    for i, hint in enumerate(scn.time_hints[1:], 1):
        hints_.append(
            data.Hint(
                level_number=level.number_in_game + 1,
                hint_number=i,
                next_hint_time=get_or_default(scn.time_hints, i + 1, hints.TimeHint(0, [])).time,
                text=hint_parts_to_text(hint.hint),
            )
        )
    return data.LevelForUpload(puzzle, hints_)


def hint_parts_to_text(hints_: list[hints.BaseHint]) -> str:
    result = []
    for hint in hints_:
        match hint:
            case hints.BaseHint(type="text"):
                assert isinstance(hint, hints.TextHint)
                transformed = hint.text
            case hints.BaseHint(type="gps" | "venue"):
                assert isinstance(hint, hints.GPSHint | hints.VenueHint)
                transformed = f"{hint.latitude},{hint.longitude}"
            case _:
                # TODO other cases #81
                transformed = f"<b>unknown {hint.type}<b>"
        result.append(transformed)

    return "\n\n".join(result)


T = TypeVar("T")


def get_or_default(sequence: Sequence[T], index: int, default: T) -> T:
    try:
        return sequence[index]
    except IndexError:
        return default
