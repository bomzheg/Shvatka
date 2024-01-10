from dataclasses import dataclass


@dataclass
class VersionInfo:
    build_at: str
    vcs_hash: str
