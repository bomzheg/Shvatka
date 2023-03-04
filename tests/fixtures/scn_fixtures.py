from io import BytesIO
from pathlib import Path

import pytest
import yaml

from src.core.models.dto.scn.game import RawGameScenario

GUID = "a3bc9b96-3bb8-4dbc-b996-ce1015e66e53"
GUID_2 = "83e6a132-5c25-4fb1-8683-29ad498e90d8"


@pytest.fixture
def complex_scn(fixtures_resource_path: Path) -> RawGameScenario:
    with open(fixtures_resource_path / "complex_scn.yml", "r", encoding="utf-8") as f:
        return RawGameScenario(
            scn=yaml.safe_load(f.read()),
            files={GUID: BytesIO(b"123")},
        )


@pytest.fixture
def simple_scn(fixtures_resource_path: Path) -> RawGameScenario:
    with open(fixtures_resource_path / "simple_scn.yml", "r", encoding="utf-8") as f:
        return RawGameScenario(
            scn=yaml.safe_load(f.read()),
            files={},
        )


@pytest.fixture
def three_lvl_scn(fixtures_resource_path: Path) -> RawGameScenario:
    with open(fixtures_resource_path / "three_lvl_scn.yml", "r", encoding="utf-8") as f:
        return RawGameScenario(
            scn=yaml.safe_load(f.read()),
            files={},
        )


@pytest.fixture
def all_types_scn(fixtures_resource_path: Path) -> RawGameScenario:
    with open(fixtures_resource_path / "all_types.yml", "r", encoding="utf-8") as f:
        return RawGameScenario(
            scn=yaml.safe_load(f),
            files={GUID: BytesIO(b"123"), GUID_2: BytesIO(b"890")},
        )
