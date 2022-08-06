from pathlib import Path

import pytest
import yaml


@pytest.fixture
def simple_scn(fixtures_resource_path: Path) -> dict:
    with open(fixtures_resource_path / 'simple_scn.yml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f.read())
