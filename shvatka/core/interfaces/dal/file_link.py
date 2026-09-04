from collections.abc import Collection
from typing import Protocol


class FileIdsByGuidsGetter(Protocol):
    async def get_ids_by_guids(self, guids: Collection[str]) -> list[int]:
        raise NotImplementedError


class LevelFilesSyncer(Protocol):
    async def sync_level_files(self, level_id: int, file_ids: Collection[int]) -> None:
        raise NotImplementedError


class GameFilesAdder(Protocol):
    async def add_game_files(self, game_id: int, file_ids: Collection[int]) -> None:
        raise NotImplementedError


class LevelFilesDeleter(Protocol):
    async def delete_level_files(self, level_id: int) -> None:
        raise NotImplementedError


class LevelFilesSyncDao(FileIdsByGuidsGetter, LevelFilesSyncer, GameFilesAdder, Protocol):
    pass
