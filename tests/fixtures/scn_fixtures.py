from copy import deepcopy
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def complex_scn(fixtures_resource_path: Path) -> dict:
    with open(fixtures_resource_path / 'simple_scn.yml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f.read())


@pytest.fixture
def simple_scn(complex_scn: dict) -> dict:
    scn = deepcopy(complex_scn)
    scn["files"] = []
    scn["levels"][0]["time-hints"][1]["hint"][0] = {"type": "text", "text": "подсказка"}
    return scn
