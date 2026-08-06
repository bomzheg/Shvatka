"""The sheet of keys an org prints, cuts and takes to the game.

The layout is checked with a made up font where every character is the same
width — the real one only makes the numbers less round.
"""

import uuid
from datetime import datetime

import pytest

from shvatka.core.models import dto
from shvatka.core.models.dto import action, hints, scn
from shvatka.core.models.enums import GameStatus
from shvatka.core.scenario import dto as scenario_dto
from shvatka.core.scenario.interactors import AllGameKeysPrintInteractor
from shvatka.core.utils.datetime_utils import tz_game
from shvatka.infrastructure.printer import keys_layout
from shvatka.infrastructure.printer.keys_layout import (
    CONTENT_HEIGHT_MM,
    CONTENT_WIDTH_MM,
    KEY_FONT_MAX_PT,
    MARGIN_MM,
    PAGE_HEIGHT_MM,
    PAGE_WIDTH_MM,
    PT_IN_MM,
    KeysSheetLayout,
    Sheet,
)
from tests.fixtures.identity import MockIdentityProvider

CHAR_WIDTH_EM = 0.6

AMNESIA_KEYS = [
    "СХПОЛОСАТЫЙРЕЙС",
    "СХНЕВЛЕЗАЙУБЬЮ",
    "СХБОБРКУРВАЩАВПЕРДОЛЮ",
    "СХМАТЬДРАКОШИ",
    "СХСМОТРЯКАКОЙФЭБРИК",
    "СХДЫРЯВЫЙГАНДОН",
    "СХВКУСНОИГРУСТНО",
    "СХКРОШКАЕНОТ",
    "СХГОЛОПОМСКАЧИКОНЯГА",
    "СХ875550",
    "СХНЕДЫШИНЕМОРГАЙ",
    "СХРЫБАЯЗЬЗДОРОВЕННЫЙ",
    "СХБУКЕНГЕМСКИЙГЕЙ",
    "СХКОТИКИНАРКОТИКИ",
    "СХСОВИНЬОНКАБЕРНЕ",
    "СХМАМБОИТАЛИАНО",
    "СХТЫВСПОМНИЛНАЧАЛО",
]
"""Keys of a game that really was played — the one the printed page comes from."""


def measure(text: str, font_pt: float) -> float:
    return len(text) * CHAR_WIDTH_EM * font_pt * PT_IN_MM


@pytest.fixture
def layout() -> KeysSheetLayout:
    return KeysSheetLayout(measure)


def sheet_of(*keys: str, name: str = "Амнезия") -> scenario_dto.KeysSheet:
    return scenario_dto.KeysSheet(
        game_name=name,
        game_date=datetime(2024, 7, 6, 23, 0, tzinfo=tz_game),
        keys=list(keys),
    )


def printed(sheet: Sheet) -> list[str]:
    return ["".join(slip.lines) for page in sheet.pages for slip in page.slips]


def test_every_key_is_printed_the_same_number_of_times(layout: KeysSheetLayout):
    keys = [f"СХКЛЮЧНОМЕР{i}" for i in range(1, 18)]

    sheet = layout.plan(sheet_of(*keys))

    assert len(sheet.pages) == 1
    assert sheet.copies > 1, "17 short keys leave enough room on A4 for doubles"
    assert {printed(sheet).count(key) for key in keys} == {sheet.copies}


def test_keys_barely_fitting_are_printed_once(layout: KeysSheetLayout):
    keys = [f"СХОЧЕНЬДЛИННЫЙКЛЮЧСНОМЕРОМ{i}" for i in range(200)]

    sheet = layout.plan(sheet_of(*keys))

    assert sheet.copies == 1
    assert printed(sheet) == keys
    assert len(sheet.pages) > 1, "200 keys don't fit on a single sheet"


def test_key_signed_with_game_name_and_date(layout: KeysSheetLayout):
    sheet = layout.plan(sheet_of("СХКЛЮЧ"))

    slip = sheet.pages[0].slips[0]
    assert slip.caption_name == "Игра: Амнезия"
    assert slip.caption_date == "06.07.24"


def test_long_game_name_is_shortened_to_the_slip(layout: KeysSheetLayout):
    sheet = layout.plan(sheet_of("СХКЛЮЧ", name="Игра с невероятно длинным названием" * 20))

    slip = sheet.pages[0].slips[0]
    assert slip.caption_name.endswith("…")
    assert (
        layout.caption_width(slip.caption_name, slip.caption_date, slip.caption_font_pt)
        <= slip.width
    )


def test_abnormal_key_gets_pages_of_its_own(layout: KeysSheetLayout):
    """We once had a key of more than 200 characters — it fits nowhere in a grid."""
    abnormal = "СХ" + "ОЧЕНЬДЛИННЫЙКЛЮЧ" * 20

    sheet = layout.plan(sheet_of("СХКЛЮЧ", abnormal, "СХДРУГОЙКЛЮЧ"))

    grid, own = sheet.pages[0], sheet.pages[1]
    assert {"".join(slip.lines) for slip in grid.slips} == {"СХКЛЮЧ", "СХДРУГОЙКЛЮЧ"}
    assert {"".join(slip.lines) for slip in own.slips} == {abnormal}
    assert all(len(slip.lines) > 1 for slip in own.slips), "such a key can't be one line"


def test_grid_is_not_broken_by_a_single_key(layout: KeysSheetLayout):
    sheet = layout.plan(sheet_of("СХЕДИНСТВЕННЫЙКЛЮЧ"))

    assert len(sheet.pages) == 1
    assert sheet.copies == len(sheet.pages[0].slips)


def test_nothing_is_printed_over_the_margins(layout: KeysSheetLayout):
    sheet = layout.plan(sheet_of(*[f"СХКЛЮЧ{i}" for i in range(30)], "СХ" + "ДЛИННЫЙ" * 30))

    for page in sheet.pages:
        for slip in page.slips:
            assert slip.left >= MARGIN_MM
            assert slip.top >= MARGIN_MM
            assert slip.left + slip.width <= PAGE_WIDTH_MM - MARGIN_MM + 1e-9
            assert slip.top + slip.height <= PAGE_HEIGHT_MM - MARGIN_MM + 1e-9


def test_keys_are_as_large_as_they_fit(layout: KeysSheetLayout):
    sheet = layout.plan(sheet_of("СХ1", "СХ" + "Д" * 70))

    tiny, wide = sheet.pages[0].slips[0], sheet.pages[0].slips[-1]
    assert tiny.font_pt == KEY_FONT_MAX_PT, "a short key is printed at the largest size"
    assert wide.font_pt < KEY_FONT_MAX_PT
    assert measure(wide.lines[0], wide.font_pt) <= wide.width


def test_columns_grow_when_keys_are_short(layout: KeysSheetLayout):
    wide = layout.plan(sheet_of(*[f"СХОЧЕНЬДЛИННЫЙКЛЮЧ{i}" for i in range(8)]))
    narrow = layout.plan(sheet_of(*[f"СХ{i}" for i in range(8)]))

    assert columns_of(narrow) > columns_of(wide)


def test_wrapping_keeps_every_character(layout: KeysSheetLayout):
    key = "СХ" + "ДЛИННЫЙКЛЮЧ" * 25

    lines = layout.wrap(key, KEY_FONT_MAX_PT, CONTENT_WIDTH_MM)

    assert "".join(lines) == key
    assert all(measure(line, KEY_FONT_MAX_PT) <= CONTENT_WIDTH_MM for line in lines)


def test_page_is_filled_by_the_grid(layout: KeysSheetLayout):
    sheet = layout.plan(sheet_of(*[f"СХКЛЮЧ{i}" for i in range(12)]))

    slips = sheet.pages[0].slips
    assert slips[-1].top + slips[-1].height == pytest.approx(PAGE_HEIGHT_MM - MARGIN_MM)


def test_empty_sheet_has_no_pages(layout: KeysSheetLayout):
    assert layout.plan(sheet_of()).pages == ()


def test_slip_height_leaves_room_for_the_key_and_the_caption(layout: KeysSheetLayout):
    assert layout.slip_height() < CONTENT_HEIGHT_MM
    assert layout.slip_height() > KEY_FONT_MAX_PT * PT_IN_MM


def columns_of(sheet: Sheet) -> int:
    tops = [slip.top for slip in sheet.pages[0].slips]
    return tops.count(tops[0])


def test_real_font_makes_the_sheet_of_the_game_document():
    """A game of ordinary keys comes out as the orgs used to lay it out by hand.

    Times New Roman (or the stand-in this machine has instead), keys at 14 pt,
    signed at 10 pt — and every key printed more than once.
    """
    from shvatka.infrastructure.printer import keys_sheet

    printer = keys_sheet.PdfKeysSheetPrinter()
    sheet = printer.layout.plan(sheet_of(*AMNESIA_KEYS))

    assert keys_sheet.FONT in keys_sheet.FONT_FAMILIES, "no font of the list was found"
    slips = [slip for page in sheet.pages for slip in page.slips]
    assert {slip.font_pt for slip in slips} == {keys_layout.KEY_FONT_MAX_PT}
    assert {slip.caption_font_pt for slip in slips} == {keys_layout.CAPTION_FONT_PT}
    assert len(sheet.pages) == 1
    assert sheet.copies >= 2
    assert printer.print_keys_sheet(sheet_of("СХКЛЮЧ")).getvalue().startswith(b"%PDF")


@pytest.mark.asyncio
async def test_interactor_prints_every_key_of_the_game_once():
    game = make_game(
        [("СХПЕРВЫЙ",), ("СХВТОРОЙ", "СХБОНУС"), ("СХПЕРВЫЙ",)],
    )
    printer = RecordingPrinter()
    interactor = AllGameKeysPrintInteractor(dao=FakeGameDao(game), printer=printer)

    await interactor(game.id, MockIdentityProvider(player=game.author))

    assert printer.sheet is not None
    assert printer.sheet.game_name == game.name
    assert printer.sheet.game_date == game.start_at
    assert printer.sheet.keys == ["СХПЕРВЫЙ", "СХВТОРОЙ", "СХБОНУС"]


class RecordingPrinter:
    file_extension = "pdf"

    def __init__(self) -> None:
        self.sheet: scenario_dto.KeysSheet | None = None

    def print_keys_sheet(self, sheet: scenario_dto.KeysSheet):
        self.sheet = sheet


class FakeGameDao:
    def __init__(self, game: dto.FullGame) -> None:
        self.game = game

    async def get_full(self, id_: int) -> dto.FullGame:
        return self.game


def make_game(levels_keys: list[tuple[str, ...]]) -> dto.FullGame:
    author = dto.Player(id=1, can_be_author=True, is_dummy=False, username="author")
    levels = [
        dto.GamedLevel(
            db_id=i,
            name_id=f"level{i}",
            author=author,
            scenario=scn.LevelScenario(
                id=f"level{i}",
                time_hints=scn.HintsList(
                    [hints.TimeHint(time=0, hint=[hints.TextHint(text="загадка")])]
                ),
                conditions=scn.Conditions(
                    [action.KeyWinCondition({keys[0]})]
                    + [
                        action.KeyEffectsCondition(
                            keys={key},
                            effects=action.Effects(id=uuid.uuid4(), bonus_minutes=10),
                        )
                        for key in keys[1:]
                    ]
                ),
                __model_version__=1,
            ),
            game_id=10,
            number_in_game=i,
        )
        for i, keys in enumerate(levels_keys)
    ]
    return dto.FullGame(
        id=10,
        author=author,
        name="Амнезия",
        status=GameStatus.complete,
        manage_token="token",
        start_at=datetime(2024, 7, 6, 23, 0, tzinfo=tz_game),
        number=5,
        results=dto.GameResults(
            published_chanel_id=None,
            results_picture_file_id=None,
            keys_url=None,
        ),
        levels=levels,
    )
