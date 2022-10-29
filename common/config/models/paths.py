from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Paths:
    app_dir: Path

    @property
    def config_path(self) -> Path:
        return self.app_dir / "config"

    @property
    def logging_config_file(self) -> Path:
        return self.config_path / "logging.yml"

    @property
    def log_path(self) -> Path:
        return self.app_dir / "log"
