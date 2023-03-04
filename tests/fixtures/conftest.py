import pytest

from shvatka.common import Paths


@pytest.fixture
def fixtures_resource_path(paths: Paths):
    return paths.app_dir / "fixtures" / "resources"
