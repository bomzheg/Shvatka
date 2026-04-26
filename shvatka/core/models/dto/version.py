from dataclasses import dataclass


@dataclass(kw_only=True, slots=True, frozen=True)
class VersionInfo:
    build_at: str | None = None
    vcs_hash: str | None = None
    commit_at: str | None = None
    vcs_name: str | None = None
