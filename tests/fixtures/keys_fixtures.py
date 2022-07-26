from pathlib import Path

import pytest


@pytest.fixture
def valid_keys(fixtures_resource_path: Path):
    with open(fixtures_resource_path / 'valid_keys.txt', 'r', encoding='utf-8') as keys_file:
        return strip_list(keys_file.readlines())


@pytest.fixture
def wrong_keys(fixtures_resource_path: Path):
    with open(fixtures_resource_path / 'wrong_keys.txt', 'r', encoding='utf-8') as keys_file:
        return strip_list(keys_file.readlines())


def strip_list(lst: list[str]) -> list[str]:
    return list(map(lambda line: line.strip(), lst))
