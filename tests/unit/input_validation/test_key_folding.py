import pytest

from shvatka.core.utils.input_validation import is_key_valid, normalize_key
from shvatka.core.utils.key_folding import CONFUSABLE_GROUPS, fold_key, fold_keys

# a look-alike character is invisible in the source too, so every one of them is
# spelled by its code point here
CYRILLIC_ES = "\u0421"  # looks like latin C
CYRILLIC_HA = "\u0425"  # looks like latin X
CYRILLIC_A = "\u0410"  # looks like latin A
CYRILLIC_KA = "\u041a"  # looks like latin K
CYRILLIC_O = "\u041e"  # looks like latin O
CYRILLIC_TE = "\u0422"  # looks like latin T
CYRILLIC_IE = "\u0415"  # looks like latin E
CYRILLIC_IO = "\u0401"  # cyrillic io
CYRILLIC_ZE = "\u0417"  # looks like the digit 3
CYRILLIC_CHE = "\u0427"  # looks like the digit 4
CYRILLIC_BE = "\u0411"  # cyrillic be, kept apart from the digit 6
CYRILLIC_DZE = "\u0405"  # looks like latin S
CYRILLIC_I = "\u0406"  # looks like latin I
LATIN_E_DIAERESIS = "\u00cb"  # looks like cyrillic io
GREEK_KAPPA = "\u03ba"  # not a key character at all


@pytest.mark.parametrize(
    ("first", "second"),
    [
        pytest.param("SHKOT", f"SH{CYRILLIC_KA}{CYRILLIC_O}{CYRILLIC_TE}", id="cyrillic-body"),
        pytest.param("SHKOT", f"SH{CYRILLIC_KA}OT", id="one-cyrillic-letter"),
        pytest.param("SHO0", "SH00", id="letter-o-and-zero"),
        pytest.param("SHI1", "SH11", id="letter-i-and-one"),
        pytest.param("SH3", f"SH{CYRILLIC_ZE}", id="three-and-cyrillic-ze"),
        pytest.param("SH4", f"SH{CYRILLIC_CHE}", id="four-and-cyrillic-che"),
        pytest.param(
            f"SH{CYRILLIC_IE}{CYRILLIC_A}", f"SH{CYRILLIC_IO}{CYRILLIC_A}", id="ie-and-io"
        ),
        pytest.param(f"SH{CYRILLIC_IO}", f"SH{LATIN_E_DIAERESIS}", id="cyrillic-io-and-latin-e"),
        pytest.param(f"{CYRILLIC_ES}{CYRILLIC_HA}123", "CX123", id="prefix"),
        pytest.param("SH123", f"{CYRILLIC_DZE}H123", id="prefix-cyrillic-dze"),
    ],
)
def test_look_alike_keys_are_one_key(first: str, second: str):
    assert first != second
    assert fold_key(first) == fold_key(second)


@pytest.mark.parametrize(
    ("first", "second"),
    [
        pytest.param("SHKOT", "SHKOD", id="other-letter"),
        pytest.param("SHKOT", "SHKO", id="shorter"),
        pytest.param("SH123", f"{CYRILLIC_ES}{CYRILLIC_HA}123", id="other-prefix"),
        pytest.param("SHb", "SHB", id="case"),
        pytest.param("SH5", "SHS", id="five-and-es-are-apart"),
        pytest.param("SH6", f"SH{CYRILLIC_BE}", id="six-and-be-are-apart"),
    ],
)
def test_different_keys_stay_different(first: str, second: str):
    assert fold_key(first) != fold_key(second)


def test_folding_keeps_length():
    key = f"SH{CYRILLIC_KA}{CYRILLIC_O}{CYRILLIC_TE}1{CYRILLIC_IO}"
    assert len(fold_key(key)) == len(key)


def test_every_character_folds_to_the_representative():
    for group in CONFUSABLE_GROUPS:
        for char in group:
            assert fold_key(char) == group[0]
            assert fold_key(fold_key(char)) == fold_key(char)


def test_representative_is_a_key_character():
    for group in CONFUSABLE_GROUPS:
        assert is_key_valid(f"SH{group[0]}"), group


def test_fold_keys_collapses_look_alikes():
    assert fold_keys({"SHKOT", f"SH{CYRILLIC_KA}OT", "SHKOD"}) == {"SHKOT", "SHKOD"}


@pytest.mark.parametrize(
    "key",
    [
        pytest.param(f"SH{CYRILLIC_KA}OT", id="mixed-body"),
        pytest.param("CX123", id="latin-cx-prefix"),
        pytest.param(f"{CYRILLIC_DZE}H123", id="cyrillic-dze-prefix"),
        pytest.param(f"SH{LATIN_E_DIAERESIS}{CYRILLIC_A}", id="latin-e-diaeresis"),
        pytest.param(f"SH{CYRILLIC_I}", id="cyrillic-i"),
    ],
)
def test_look_alike_key_is_a_key(key: str):
    assert is_key_valid(key)
    assert normalize_key(key) == key


@pytest.mark.parametrize(
    "key",
    [
        pytest.param("SX123", id="not-a-prefix"),
        pytest.param("HS123", id="reversed-prefix"),
        pytest.param("SH", id="prefix-only"),
        pytest.param("SH-1", id="punctuation"),
        pytest.param(f"SH{GREEK_KAPPA}", id="greek-kappa"),
    ],
)
def test_look_alike_folding_keeps_wrong_keys_wrong(key: str):
    assert not is_key_valid(key)


def test_normalize_keeps_what_was_typed():
    key = f"SH{CYRILLIC_KA}OT"
    assert normalize_key(f"  {key}  ") == key
