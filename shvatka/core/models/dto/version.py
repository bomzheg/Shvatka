from dataclasses import dataclass
from datetime import datetime


@dataclass
class VersionInfo:
    build_at: datetime
    vcs_hash: str
