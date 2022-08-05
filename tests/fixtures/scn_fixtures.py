from pathlib import Path

import pytest


@pytest.fixture
def simple_scn(fixtures_resource_path: Path) -> str:
    with open(fixtures_resource_path / 'simple_scn.yml', 'r', encoding='utf-8') as id_file:
        return id_file.read()
