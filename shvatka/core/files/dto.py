from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class GameFileLink:
    id: int
    game_id: int
    file_id: int


@dataclass(frozen=True, slots=True)
class FileGarbage:
    game_links: list[GameFileLink] = field(default_factory=list)
    """``game_files`` rows for files nothing in that game refers to"""
    file_guids: list[str] = field(default_factory=list)
    """guids of ``files_info`` rows left with no link at all"""
    stored_files: list[str] = field(default_factory=list)
    """paths of stored files no meta row points to"""
    dry_run: bool = False
    """when true, nothing was deleted — the lists say what would have been"""
