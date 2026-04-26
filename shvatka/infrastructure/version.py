import yaml
from adaptix import Retort

from shvatka.common import Paths
from shvatka.core.models import dto

retort = Retort()


def get_version(paths: Paths) -> dto.VersionInfo:
    with paths.version_path.open() as version_file:
        return retort.load(yaml.safe_load(version_file), dto.VersionInfo)
