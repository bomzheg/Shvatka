import os
from pathlib import Path

from common.config.models.paths import Paths


def common_get_paths(env_var: str) -> Paths:
    if path := os.getenv(env_var):
        return Paths(Path(path))
    return Paths(Path(__file__).parent.parent)
