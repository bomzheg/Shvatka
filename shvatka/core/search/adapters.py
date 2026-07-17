from typing import Protocol

from shvatka.core.models import dto
from shvatka.core.search.dto import LevelWithGame


class GlobalSearchDao(Protocol):
    async def search_completed_games(self, text: str) -> list[dto.Game]:
        """Завершённые игры, чьё название содержит text (без учёта регистра)."""
        raise NotImplementedError

    async def search_levels_of_completed_games(self, text: str) -> list[LevelWithGame]:
        """Уровни завершённых игр, у которых text встречается в name_id или в сценарии.

        Это грубый SQL-фильтр по всему json сценария: точное место совпадения
        определяет уже интерактор, обходя сценарий в памяти.
        """
        raise NotImplementedError

    async def search_teams(self, text: str) -> list[dto.Team]:
        """Команды (включая архивные форумные), чьё название содержит text."""
        raise NotImplementedError

    async def search_players(self, text: str) -> list[dto.Player]:
        """Игроки, у которых text встречается в username, имени в tg или имени на форуме."""
        raise NotImplementedError
