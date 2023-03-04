from dataclasses import dataclass

from src.core.models import dto


@dataclass
class LevelView(dto.Level):
    @property
    def has_game(self):
        return self.game_id is not None
