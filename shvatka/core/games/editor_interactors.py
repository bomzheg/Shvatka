"""Interactors used by the web UI to create and edit game drafts.

They wrap the domain services from :mod:`shvatka.core.services.game` and operate
on internal domain models (FullGame, GameScenario, ...) so the transport layer
(api routes) stays thin.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO

from adaptix import Retort

from shvatka.core.games.adapters import GameNameEditor
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.dal.complex import GameScenarioEditor, GameStatusChanger
from shvatka.core.interfaces.dal.game import (
    GameAuthorsFinder,
    GameByIdGetter,
    GameCreator,
    GameFileDeleter,
    GameFileRenamer,
    GameFileUploader,
    GameStartPlanner,
)
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import hints
from shvatka.core.players.player import check_allow_be_author
from shvatka.core.rules.game import check_can_add_file
from shvatka.core.services.game import (
    cancel_planed_start,
    complete_game,
    create_game,
    get_authors_games,
    get_full_game,
    plain_start,
    rename_game,
    start_waivers,
    update_game_scenario,
)
from shvatka.core.services.scenario.files import rename_file, save_file
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import DATETIME_FORMAT, tz_game
from shvatka.core.views.game import (
    GameLogEvent,
    GameLogType,
    GameLogWriter,
    GameReleasePublisher,
)

logger = logging.getLogger(__name__)


@dataclass
class MyGamesInteractor:
    dao: GameAuthorsFinder

    async def __call__(self, identity: IdentityProvider) -> list[dto.Game]:
        return await get_authors_games(identity, self.dao)


@dataclass
class MyGameInteractor:
    dao: GameByIdGetter

    async def __call__(self, game_id: int, identity: IdentityProvider) -> dto.FullGame:
        return await get_full_game(game_id, identity, self.dao)


@dataclass
class CreateGameInteractor:
    dao: GameCreator

    async def __call__(self, name: str, identity: IdentityProvider) -> dto.Game:
        author = await identity.get_required_player()
        return await create_game(author=author, name=name, dao=self.dao)


@dataclass
class RenameGameInteractor:
    """Rename a game draft on its own, without touching its scenario.

    The scenario carries the name too, so saving one renames the game — but a
    game that has no levels yet has no scenario to save, and that is exactly
    when a name written in a hurry wants fixing. Hence a route of its own.
    """

    dao: GameNameEditor

    async def __call__(self, game_id: int, name: str, identity: IdentityProvider) -> dto.Game:
        author = await identity.get_required_player()
        check_allow_be_author(author)
        game = await self.dao.get_by_id(id_=game_id, author=author)
        return await rename_game(author, game, name, self.dao)


@dataclass
class ChangeGameScenarioInteractor:
    dao: GameScenarioEditor
    retort: Retort

    async def __call__(
        self, game_id: int, raw_scn: dict, identity: IdentityProvider
    ) -> dto.FullGame:
        author = await identity.get_required_player()
        return await update_game_scenario(game_id, raw_scn, author, self.dao, self.retort)


@dataclass
class PlanGameStartInteractor:
    getter: GameByIdGetter
    dao: GameStartPlanner
    scheduler: Scheduler
    game_log: GameLogWriter

    async def __call__(
        self, game_id: int, start_at: datetime | None, identity: IdentityProvider
    ) -> dto.Game:
        author = await identity.get_required_player()
        game = await self.getter.get_by_id(id_=game_id, author=author)
        if start_at is None:
            await cancel_planed_start(game, author, self.scheduler, self.dao)
        else:
            await plain_start(game, author, start_at, self.dao, self.scheduler)
            await self.game_log.log(
                GameLogEvent(
                    GameLogType.GAME_PLANED,
                    {
                        "game": game.name,
                        "at": start_at.astimezone(tz_game).strftime(DATETIME_FORMAT),
                    },
                )
            )
        return game


@dataclass
class ChangeGameStatusInteractor:
    dao: GameStatusChanger
    game_log: GameLogWriter
    release_publisher: GameReleasePublisher

    async def __call__(
        self, game_id: int, status: enums.GameStatus, identity: IdentityProvider
    ) -> dto.Game:
        author = await identity.get_required_player()
        game = await self.dao.get_by_id(id_=game_id, author=author)
        if status == enums.GameStatus.getting_waivers:
            await start_waivers(game, author, self.dao)
            await self.game_log.log(
                GameLogEvent(GameLogType.GAME_WAIVERS_STARTED, {"game": game.name})
            )
            # the release was waiting for exactly this moment to reach the channel
            release = await self.dao.get_release(game.id)
            if release is not None:
                await self.release_publisher.publish(game, release)
        elif status == enums.GameStatus.complete:
            await complete_game(game, self.dao)
        else:
            raise exceptions.CantEditGame(
                game=game,
                player=author,
                text=f"unsupported status transition to {status.name}",
            )
        return game


@dataclass
class UploadGameFileInteractor:
    storage: FileStorage
    dao: GameFileUploader

    async def __call__(
        self,
        game_id: int,
        content: BinaryIO,
        original_filename: str,
        identity: IdentityProvider,
        options: hints.FileUploadOptions = hints.DEFAULT_UPLOAD_OPTIONS,
    ) -> hints.SavedFileMeta:
        author = await identity.get_required_player()
        is_superuser = await identity.is_superuser()
        if not is_superuser:
            check_allow_be_author(author)
        game = await self.dao.get_by_id(id_=game_id, author=None if is_superuser else author)
        check_can_add_file(game, author, is_superuser)
        saved = await save_file(
            author, content, original_filename, self.storage, self.dao, options
        )
        # the file is uploaded for later use in this game even though it is not yet
        # assigned to any level, so register it as usable in the game.
        await self.dao.add_game_file(game.id, saved.id)
        await self.dao.commit()
        return saved


@dataclass
class DeleteGameFileInteractor:
    """Detach a file from a game, and delete the file itself with its last link.

    A file may be detached only while nothing in the game refers to it — neither
    a level's scenario nor the release — so the button can never break a game
    that is written already. Once the link is gone and no other game, level or
    release refers to the file, its meta row and its content go too: keeping a
    file nothing can reach any more is what fills the storage up.

    Like renaming, and unlike uploading, this changes a file that already exists
    rather than bringing a new one, so it stays the author's to do. What an
    admin needs is the broom, not this button — see
    :class:`shvatka.core.files.interactors.CollectFileGarbageInteractor`.
    """

    dao: GameFileDeleter
    storage: FileStorage

    async def __call__(
        self,
        game_id: int,
        guid: str,
        identity: IdentityProvider,
    ) -> None:
        author = await identity.get_required_player()
        check_allow_be_author(author)
        game = await self.dao.get_by_id(id_=game_id, author=author)
        check_can_add_file(game, author)

        file_ids = await self.dao.get_ids_by_guids([guid])
        if not file_ids or file_ids[0] not in await self.dao.get_game_file_ids(game.id):
            raise exceptions.FileNotFound(
                text=f"There is no file with uuid {guid} associated with game id {game.id}",
                game_id=game.id,
            )
        file_id = file_ids[0]
        meta = await self.dao.get_by_guid(guid)
        release_guids = await self.dao.get_release_guids()
        if guid in release_guids.get(game.id, frozenset()):
            raise exceptions.FileIsUsed(
                text=f"file {guid} is used by the release of game {game.id}",
                game=game,
                player=author,
                notify_user="Файл используется в релизе игры",
            )
        if await self.dao.get_level_ids_using_file(game.id, file_id):
            raise exceptions.FileIsUsed(
                text=f"file {guid} is used by a level of game {game.id}",
                game=game,
                player=author,
                notify_user="Файл используется в сценарии игры",
            )

        await self.dao.delete_game_file_link(game.id, file_id)
        content = await self._delete_orphaned_meta(guid, file_id, meta, release_guids)
        await self.dao.commit()
        if content is not None:
            # after the commit: content whose meta is gone is swept by the garbage
            # collector anyway, a meta whose content is gone is a broken download
            await self.storage.delete(content)
        logger.info("player %s deleted file %s from game %s", author.id, guid, game.id)

    async def _delete_orphaned_meta(
        self,
        guid: str,
        file_id: int,
        meta: hints.VerifiableFileMeta,
        release_guids: dict[int, set[str]],
    ) -> hints.FileContentLink | None:
        """Delete the meta if that was its last reference; answer with the content
        to remove, which is only the file's own when no other meta shares it."""
        if await self.dao.count_links_for_file(file_id):
            return None
        if any(guid in guids for guids in release_guids.values()):
            return None
        await self.dao.delete_file_meta(guid)
        path = meta.file_content_link.file_path
        if await self.dao.count_metas_with_path(path):
            return None
        return meta.file_content_link


@dataclass
class RenameGameFileInteractor:
    dao: GameFileRenamer

    async def __call__(
        self,
        game_id: int,
        guid: str,
        filename: str,
        identity: IdentityProvider,
    ) -> hints.VerifiableFileMeta:
        author = await identity.get_required_player()
        check_allow_be_author(author)
        # renaming changes a file that is already the author's, so unlike
        # uploading it is not something an admin does on their behalf
        game = await self.dao.get_by_id(id_=game_id, author=author)
        check_can_add_file(game, author)
        renamed = await rename_file(guid, game_id, filename, self.dao)
        await self.dao.commit()
        return renamed
