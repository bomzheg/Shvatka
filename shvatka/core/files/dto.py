from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class GameFileLink:
    """A row of ``game_files`` — one file made usable in one game."""

    id: int
    game_id: int
    file_id: int


@dataclass(frozen=True, slots=True)
class FileGarbage:
    """What a garbage collection run found — and, unless it was a dry run, removed.

    The three lists follow the three layers a file lives in: the link that makes
    it usable in a game, the meta row that describes it, and the content on the
    storage.
    """

    game_links: list[GameFileLink] = field(default_factory=list)
    """``game_files`` rows for files nothing in that game refers to"""
    file_guids: list[str] = field(default_factory=list)
    """guids of ``files_info`` rows left with no link at all"""
    stored_files: list[str] = field(default_factory=list)
    """paths of stored files no meta row points to"""
    dry_run: bool = False
    """when true, nothing was deleted — the lists say what would have been"""
