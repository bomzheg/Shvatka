import pytest

from shvatka.models.config.main import Paths


@pytest.fixture
def fixtures_resource_path(paths: Paths):
    return paths.app_dir / "fixtures" / "resources"
