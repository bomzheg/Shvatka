from pathlib import Path

import pytest


@pytest.fixture
def valid_id(fixtures_resource_path: Path):
    with open(fixtures_resource_path / "valid_ids.txt", "r", encoding="utf-8") as id_file:
        return id_file.readlines()


@pytest.fixture
def wrong_id(fixtures_resource_path: Path):
    with open(fixtures_resource_path / "wrong_ids.txt", "r", encoding="utf-8") as id_file:
        return id_file.readlines()
