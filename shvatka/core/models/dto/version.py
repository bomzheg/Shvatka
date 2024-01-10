from dataclasses import dataclass
from datetime import datetime


@dataclass
class VersionInfo:
    build_at: str
    vcs_hash: str
