import pytest

from shvatka.core.utils.username import (
    numbered_username,
    transliterate,
    username_from_names,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Harry", "harry"),
        ("Юрий", "yuriy"),
        ("Щёкин", "shchyokin"),
        ("Объезд", "obezd"),
        ("Гарри Поттер", "garri_potter"),
        ("Жанна д'Арк", "zhanna_d_ark"),
        ("Renée", "renee"),
        ("  Ян  ", "yan"),
        ("Ігор", "igor"),
        ("😀", ""),
        ("", ""),
    ],
)
def test_transliterate(text: str, expected: str):
    assert transliterate(text) == expected


@pytest.mark.parametrize(
    ("first_name", "last_name", "expected"),
    [
        ("Harry", "Potter", "harry_potter"),
        ("Гарри", "Поттер", "garri_potter"),
        ("Гарри", None, "garri"),
        (None, "Поттер", "potter"),
        ("Ян", "Ли", "yan_li"),
        ("Ли", None, None),  # too short for a username
        ("😀", None, None),
        (None, None, None),
        ("", "", None),
        (
            "Ааааааааааааааааааааааааааааааа",
            "Бббббббббббббббббббббббббббббббб",
            "a" * 31 + "_" + "b" * 18,
        ),
    ],
)
def test_username_from_names(first_name: str | None, last_name: str | None, expected: str | None):
    assert username_from_names(first_name, last_name) == expected


def test_numbered_username():
    assert numbered_username("harry_potter", 1) == "harry_potter_1"
    assert numbered_username("a" * 50, 12) == "a" * 47 + "_12"
