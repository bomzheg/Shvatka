from collections.abc import Collection
from datetime import datetime
import typing
from dataclasses import dataclass
from typing import Iterable

from shvatka.core.games.dto import CurrentHintsOnly, Event
from shvatka.core.interfaces.current_game import CurrentGameProvider

from shvatka.core.interfaces.dal.complex import GamePackager
from shvatka.core.games.adapters import GameFileReader, GamePlayDao
from shvatka.core.interfaces.dal.game import (
    GameUpserter,
    GameCreator,
    GameFileRenamer,
    GameFileUploader,
)
from shvatka.core.interfaces.dal.level import LevelDeleter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.core.models.dto import hints
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class FileLinkMixin:
    """Pass-through to the per-table file-link DAOs.

    These are plain operations; deciding *when* to sync (e.g. after a level
    upsert) is up to the use case, not the DAO."""

    dao: "HolderDao"

    async def get_ids_by_guids(self, guids: Collection[str]) -> list[int]:
        return await self.dao.file_info.get_ids_by_guids(guids)

    async def sync_level_files(self, level_id: int, file_ids: Collection[int]) -> None:
        await self.dao.level_file.sync_level_files(level_id, file_ids)

    async def add_game_files(self, game_id: int, file_ids: Collection[int]) -> None:
        await self.dao.game_file.add_game_files(game_id, file_ids)


class IsGameFileMixin:
    """Tells whether a file (by guid) is usable in a given game."""

    dao: "HolderDao"

    async def is_game_file(self, game_id: int, guid: str) -> bool:
        file_ids = await self.dao.file_info.get_ids_by_guids([guid])
        if not file_ids:
            return False
        return file_ids[0] in await self.dao.game_file.get_file_ids(game_id)


@dataclass
class GameUpserterImpl(FileLinkMixin, GameUpserter):
    async def upsert_game(self, author: dto.Player, scenario: scn.GameScenario) -> dto.Game:
        return await self.dao.game.upsert_game(author, scenario)

    async def upsert_gamed(
        self, author: dto.Player, scenario: scn.LevelScenario, game: dto.Game, no_in_game: int
    ) -> dto.GamedLevel:
        return await self.dao.level.upsert_gamed(author, scenario, game, no_in_game)

    async def upsert(
        self,
        author: dto.Player,
        scenario: scn.LevelScenario,
    ) -> dto.Level:
        return await self.dao.level.upsert(author, scenario)

    async def unlink_all(self, game: dto.Game) -> None:
        return await self.dao.level.unlink_all(game)

    async def upsert_file(self, file: hints.FileMeta, author: dto.Player) -> hints.SavedFileMeta:
        return await self.dao.file_info.upsert(file, author)

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        return await self.dao.file_info.check_author_can_own_guid(author, guid)

    async def is_name_available(self, name: str) -> bool:
        return await self.dao.game.is_name_available(name)

    async def is_author_game_by_name(self, name: str, author: dto.Player) -> bool:
        return await self.dao.game.is_author_game_by_name(name, author)

    async def get_game_by_name(self, name: str, author: dto.Player) -> dto.Game:
        return await self.dao.game.get_game_by_name(name=name, author=author)

    async def commit(self) -> None:
        await self.dao.commit()


@dataclass
class GameScenarioEditorImpl(GameUpserterImpl):
    """Combines game upsert, rename, reading by id and file checks for editing
    an existing game draft (identified by id) from the web UI."""

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.dao.game.get_by_id(id_, author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_)

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        return await self.dao.game.add_levels(game)

    async def rename_game(self, game: dto.Game, new_name: str) -> None:
        await self.dao.game.rename_game(game, new_name)

    async def get_by_guid(self, guid: str) -> hints.VerifiableFileMeta:
        return await self.dao.file_info.get_by_guid(guid)


@dataclass
class AdminGameScenarioEditorImpl(GameScenarioEditorImpl):
    """Scenario editor for admins: also reassigns the game's author.

    ``transfer`` moves the game to another author; ``get_player_by_id`` resolves
    the target player. Everything else is inherited from the regular editor."""

    async def transfer(self, game: dto.Game, new_author: dto.Player) -> None:
        await self.dao.game.transfer(game, new_author)

    async def get_player_by_id(self, id_: int) -> dto.Player:
        return await self.dao.player.get_by_id(id_)


@dataclass
class GameCreatorImpl(FileLinkMixin, GameCreator):
    async def create_game(self, author: dto.Player, name: str) -> dto.Game:
        return await self.dao.game.create_game(author, name)

    async def link_to_game(self, level: dto.Level, game: dto.Game) -> dto.GamedLevel:
        return await self.dao.level.link_to_game(level, game)

    async def commit(self) -> None:
        return await self.dao.commit()

    async def is_name_available(self, name: str) -> bool:
        return await self.dao.game.is_name_available(name)


@dataclass
class LevelDeleterImpl(LevelDeleter):
    """Deletes a level together with its file links (no DB cascade)."""

    dao: "HolderDao"

    async def delete_level_files(self, level_id: int) -> None:
        await self.dao.level_file.delete_for_level(level_id)

    async def delete(self, level_id: int) -> None:
        await self.dao.level.delete(level_id)

    async def commit(self) -> None:
        await self.dao.commit()


@dataclass
class GameFileUploaderImpl(GameFileUploader):
    """Single DAO for uploading a file directly for a game (cdn endpoint)."""

    dao: "HolderDao"

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.dao.game.get_by_id(id_, author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_)

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        return await self.dao.game.add_levels(game)

    async def upsert(self, file: hints.FileMeta, author: dto.Player) -> hints.SavedFileMeta:
        return await self.dao.file_info.upsert(file, author)

    async def check_author_can_own_guid(self, author: dto.Player, guid: str) -> None:
        return await self.dao.file_info.check_author_can_own_guid(author, guid)

    async def add_game_file(self, game_id: int, file_id: int) -> None:
        await self.dao.game_file.add_game_files(game_id, [file_id])

    async def commit(self) -> None:
        await self.dao.commit()


@dataclass
class GameFileRenamerImpl(IsGameFileMixin, GameFileRenamer):
    """Single DAO for renaming a file usable in a game (cdn endpoint)."""

    dao: "HolderDao"

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.dao.game.get_by_id(id_, author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_)

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        return await self.dao.game.add_levels(game)

    async def rename_file(self, guid: str, filename: str) -> None:
        await self.dao.file_info.rename_file(guid, filename)

    async def get_by_guid(self, guid: str) -> hints.VerifiableFileMeta:
        return await self.dao.file_info.get_by_guid(guid)

    async def commit(self) -> None:
        await self.dao.commit()


@dataclass
class GamePackagerImpl(GamePackager):
    dao: "HolderDao"

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        return await self.dao.waiver.get_played_teams(game)

    async def get_played(self, game: dto.Game, team: dto.Team) -> Iterable[dto.VotedPlayer]:
        return await self.dao.waiver.get_played(game, team)

    async def get_all_by_game(self, game: dto.Game) -> list[dto.Waiver]:
        return await self.dao.waiver.get_all_by_game(game)

    async def get_typed_keys_grouped(self, game: dto.Game) -> dict[dto.Team, list[dto.KeyTime]]:
        return await self.dao.key_time.get_typed_key_grouped(game)

    async def get_game_level_times(self, game: dto.Game) -> list[dto.LevelTime]:
        return await self.dao.level_time.get_game_level_times(game)

    async def get_game_level_times_by_teams(
        self, game: dto.Game
    ) -> dict[dto.Team, list[dto.LevelTime]]:
        return await self.dao.level_time.get_game_level_times_by_teams(game)

    async def get_game_level_times_with_hints(
        self, game: dto.FullGame
    ) -> dict[dto.Team, list[dto.LevelTimeOnGame]]:
        return await self.dao.level_time.get_game_level_times_with_hints(game)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_)

    async def get_by_guid(self, guid: str) -> hints.VerifiableFileMeta:
        return await self.dao.file_info.get_by_guid(guid)

    async def get_game_file_ids(self, game_id: int) -> set[int]:
        return await self.dao.game_file.get_file_ids(game_id)

    async def get_metas_by_ids(self, file_ids: Collection[int]) -> list[hints.VerifiableFileMeta]:
        return await self.dao.file_info.get_metas_by_ids(file_ids)


class GameFilesGetterImpl(IsGameFileMixin, GameFileReader):
    def __init__(self, dao: "HolderDao"):
        self.dao = dao

    async def get_by_guid(self, guid: str) -> hints.VerifiableFileMeta:
        return await self.dao.file_info.get_by_guid(guid)

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.dao.game.get_by_id(id_, author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_)

    async def add_levels(self, game: dto.Game) -> dto.FullGame:
        return await self.dao.game.add_levels(game)

    async def get_by_user(self, user: dto.User) -> dto.Player:
        return await self.dao.player.get_by_user(user)

    async def check_waiver(self, player: dto.Player, team: dto.Team, game: dto.Game) -> bool:
        return await self.dao.waiver.check_waiver(player, team, game)


@dataclass(kw_only=True, slots=True)
class CacheItem:
    level_time: dto.LevelTime | None = None


@dataclass(kw_only=True, slots=True)
class GamePlayDaoImpl(GamePlayDao):
    dao: "HolderDao"
    current_game: CurrentGameProvider
    cache: dict[int, CacheItem]

    async def get_current_hints(self, identity: IdentityProvider) -> CurrentHintsOnly:
        game = await self.current_game.get_required_full_game()
        level_time = await self.get_level_time(identity)
        if level_time.has_finished(game):
            is_finished = True
            hints_ = []
        else:
            is_finished = False
            level = await self.dao.level.get_by_number(game, level_time.level_number)
            td = datetime.now(tz=tz_utc) - level_time.start_at
            hints_ = level.get_hints_for_timedelta(td)
        return CurrentHintsOnly(
            hints=hints_,
            level_number=level_time.level_number,
            game_id=game.id,
            started_at=level_time.start_at,
            level_time_id=level_time.id,
            is_finished=is_finished,
        )

    async def get_team_typed_keys(self, identity: IdentityProvider) -> list[dto.InsertedKey]:
        level_time = await self.get_level_time(identity)
        game = await self.current_game.get_required_game()
        team = await identity.get_required_team()
        keys = await self.dao.key_time.get_team_inserted_keys(game, team, level_time)
        return keys

    async def get_level_time(self, identity: IdentityProvider) -> dto.LevelTime:
        user_id = await identity.get_required_user_db_id()
        if (level_time := self.cache.setdefault(user_id, CacheItem()).level_time) is not None:
            return level_time
        player = await identity.get_required_player()
        team = await identity.get_required_team()
        game = await self.current_game.get_required_game()
        if not await self.check_waivers(identity):
            raise exceptions.WaiverError(
                team=team,
                game=game,
                player=player,
                text="игрок не заявлен на игру, но пытается участвовать",
            )
        level_time = await self.dao.level_time.get_current_level_time(team, game)
        self.cache[user_id].level_time = level_time
        return level_time

    async def check_waivers(self, identity: IdentityProvider) -> bool:
        return await self.current_game.is_player_played(identity)

    async def get_effects(self, identity: IdentityProvider) -> list[dto.GameEvent]:
        return await self.dao.events.get_team_events(
            team=await identity.get_required_team(),
            game_id=(await self.current_game.get_required_game()).id,
        )

    async def get_events(
        self,
        identity: IdentityProvider,
    ) -> list[Event]:
        return await self.dao.events.get_team_events_with_source(
            team=await identity.get_required_team(),
            game_id=(await self.current_game.get_required_game()).id,
        )
