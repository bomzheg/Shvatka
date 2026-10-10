"""
Comparison form of a key.

A player types a key on whatever keyboard layout is at hand, from a photo, a
sign or a note, so a key travels through characters that are drawn the same but
are different code points: the cyrillic letter that looks like `A`, the one that
looks like `O` - or the digit `0` - and `Ё` written where the author wrote `Е`.
None of that is a mistake worth losing a level for, so keys are compared by
their *folded* form: every character is replaced by the representative of the
group of characters it can't be told apart from.

Folding is comparison-only. What the author wrote and what the player typed are
stored and shown as they are; `fold_key` is applied at every place where two
keys meet.

Look-alike characters are invisible in the source, so every non-ascii one is
spelled by its code point below.
"""

from collections.abc import Iterable

#: Groups of characters a key can't distinguish, representative first. A pair
#: belongs here when the two characters are drawn the same in the fonts a key is
#: read in (latin and cyrillic twins, `O` and zero), or when writing routinely
#: substitutes one for the other (cyrillic ie for cyrillic io, `4` for the
#: cyrillic che).
#: Characters that merely look related (`5` and `S`, `6` and the cyrillic be)
#: are left apart - folding them would cost more keys than it saves.
#: The representative is the latin letter or the digit, so a folded key stays
#: readable in a log.
CONFUSABLE_GROUPS: tuple[tuple[str, ...], ...] = (
    ("A", "А"),  # cyrillic a
    ("B", "В"),  # cyrillic ve
    ("C", "С"),  # cyrillic es
    ("E", "Е", "Ё", "Ë"),  # cyrillic ie, cyrillic io, latin e with diaeresis
    ("H", "Н"),  # cyrillic en
    ("I", "І", "1"),  # cyrillic byelorussian-ukrainian i, digit one
    ("J", "Ј"),  # cyrillic je
    ("K", "К"),  # cyrillic ka
    ("M", "М"),  # cyrillic em
    ("O", "О", "0"),  # cyrillic o, digit zero
    ("P", "Р"),  # cyrillic er
    ("S", "Ѕ"),  # cyrillic dze
    ("T", "Т"),  # cyrillic te
    ("X", "Х"),  # cyrillic ha
    ("Y", "У", "Ү"),  # cyrillic u, cyrillic straight u
    ("3", "З"),  # cyrillic ze
    ("4", "Ч"),  # cyrillic che
)

FOLDING_TABLE = str.maketrans(
    {alias: group[0] for group in CONFUSABLE_GROUPS for alias in group[1:]}
)


def fold_key(key: str) -> str:
    """Return the form of the key two keys are compared by. Keeps the length."""
    return key.translate(FOLDING_TABLE)


def fold_keys(keys: Iterable[str]) -> set[str]:
    """Comparison forms of the keys. Keys folding into one another collapse."""
    return {fold_key(key) for key in keys}
