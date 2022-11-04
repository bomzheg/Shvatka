from io import BytesIO
from pathlib import Path

import pytest
import yaml

from shvatka.models.dto.scn.game import RawGameScenario


@pytest.fixture
def complex_scn(fixtures_resource_path: Path) -> RawGameScenario:
    with open(fixtures_resource_path / 'complex_scn.yml', 'r', encoding='utf-8') as f:
        return RawGameScenario(
            scn=yaml.safe_load(f.read()),
            files={"a3bc9b96-3bb8-4dbc-b996-ce1015e66e53": BytesIO(b"123")},
        )


@pytest.fixture
def simple_scn(fixtures_resource_path: Path) -> RawGameScenario:
    with open(fixtures_resource_path / 'simple_scn.yml', 'r', encoding='utf-8') as f:
        return RawGameScenario(
            scn=yaml.safe_load(f.read()),
            files={},
        )

