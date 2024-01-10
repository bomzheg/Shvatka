import dataclass_factory
import yaml

from shvatka.common import Paths
from shvatka.core.models import dto

dcf = dataclass_factory.Factory()


def get_version(paths: Paths) -> dto.VersionInfo:
    with paths.version_path.open() as version_file:
        return dcf.load(yaml.safe_load(version_file), dto.VersionInfo)
