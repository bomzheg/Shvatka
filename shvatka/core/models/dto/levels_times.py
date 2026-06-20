from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .game import Game, FullGame
from .team import Team


@dataclass
class LevelTime:
    id: int
    game: Game
    team: Team
    level_number: int
    start_at: datetime

    def to_on_game(
        self,
        game: FullGame,
        hint: SpyHintInfo | None,
        name_id: str | None = None,
    ) -> LevelTimeOnGame:
        return LevelTimeOnGame(
            id=self.id,
            game=self.game,
            team=self.team,
            level_number=self.level_number,
            start_at=self.start_at,
            is_finished=self.has_finished(game),
            hint=hint,
            name_id=name_id,
        )

    def has_finished(self, game: FullGame) -> bool:
        return self.level_number >= len(game.levels)

    def __repr__(self) -> str:
        return (
            f"<LevelTime team={self.team} level_number={self.level_number} "
            f"at={self.start_at.isoformat()}>"
        )


@dataclass
class SpyHintInfo:
    number: int
    time: int
    """minutes"""


@dataclass
class LevelTimeOnGame(LevelTime):
    is_finished: bool
    hint: SpyHintInfo | None
    name_id: str | None
    """name_id of the current level; None when the team has finished the game."""

    def __repr__(self) -> str:
        return super().__repr__()


@dataclass
class GameStat:
    level_times: dict[Team, list[LevelTime]]


@dataclass
class GameStatWithHints:
    level_times: dict[Team, list[LevelTimeOnGame]]
