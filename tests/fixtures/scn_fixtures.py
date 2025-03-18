from io import BytesIO
from pathlib import Path

import pytest
import yaml

from shvatka.core.models.dto.scn.game import RawGameScenario

GUID = "a3bc9b96-3bb8-4dbc-b996-ce1015e66e53"
GUID_2 = "83e6a132-5c25-4fb1-8683-29ad498e90d8"


@pytest.fixture
def complex_scn(fixtures_resource_path: Path) -> RawGameScenario:
    return _load_game_scn(fixtures_resource_path / "complex_scn.yml", {GUID: BytesIO(b"123")})


@pytest.fixture
def simple_scn(fixtures_resource_path: Path) -> RawGameScenario:
    return _load_game_scn(fixtures_resource_path / "simple_scn.yml", {})


@pytest.fixture
def three_lvl_scn(fixtures_resource_path: Path) -> RawGameScenario:
    return _load_game_scn(fixtures_resource_path / "three_lvl_scn.yml", {})


@pytest.fixture
def all_types_scn(fixtures_resource_path: Path) -> RawGameScenario:
    return _load_game_scn(
        fixtures_resource_path / "all_types.yml", {GUID: BytesIO(b"123"), GUID_2: BytesIO(b"890")}
    )


@pytest.fixture
def routed_scn(fixtures_resource_path: Path) -> RawGameScenario:
    return _load_game_scn(fixtures_resource_path / "routed_scn.yml", {})


@pytest.fixture
def no_file_guid_scn(fixtures_resource_path: Path) -> RawGameScenario:
    return _load_game_scn(fixtures_resource_path / "scn_no_file_guid.yml", {GUID: BytesIO(b"123")})


def _load_game_scn(path: Path, files: dict[str, BytesIO]):
    with path.open("r", encoding="utf8") as f:
        return RawGameScenario(
            scn=yaml.safe_load(f),
            files=files,
        )
