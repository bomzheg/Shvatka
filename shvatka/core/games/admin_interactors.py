"""Interactors backing admin edits of existing (including completed) games.

Unlike the author-facing editor interactors in :mod:`editor_interactors`, these
take the acting user via an ``IdentityProvider`` and authorise through
``identity.get_superuser()``. They deliberately skip the ``check_game_editable``
guard and the game-ownership check, so an admin may edit a game in any status
(e.g. an already completed one), reassign its author and upload new media files.
"""

import logging
from dataclasses import dataclass
from typing import BinaryIO

from adaptix import Retort

from shvatka.core.games.adapters import AdminGameScenarioEditor
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.dal.game import GameFileUploader
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.dto import hints, scn
from shvatka.core.players.player import check_allow_be_author
from shvatka.core.services.scenario.files import save_file, sync_files_for_level
from shvatka.core.services.scenario.game_ops import parse_uploaded_game
from shvatka.core.utils.exceptions import CantEditGame

logger = logging.getLogger(__name__)


@dataclass
class AdminUpdateGameScenarioInteractor:
    dao: AdminGameScenarioEditor
    retort: Retort

    async def __call__(
        self,
        game_id: int,
        raw_scn: dict,
        identity: IdentityProvider,
        new_author_id: int | None = None,
    ) -> dto.FullGame:
        """Replace the whole scenario of any game, regardless of its status.

        Files are expected to be already uploaded (only their guids are
        referenced). When ``new_author_id`` is given, the game (and the levels
        upserted here) is reassigned to that player first.
        """
        admin = await identity.get_superuser()
        game_scn = parse_uploaded_game(scn.RawGameScenario(scn=raw_scn, files={}), self.retort)
        game = await self.dao.get_by_id(id_=game_id)
        if new_author_id is not None and new_author_id != game.author.id:
            new_author = await self.dao.get_player_by_id(new_author_id)
            check_allow_be_author(new_author)
            await self.dao.transfer(game, new_author)
            logger.warning(
                "admin %s changed author of game %s to player %s",
                admin.id,
                game.id,
                new_author.id,
            )
            game.author = new_author
        author = game.author
        if game.name != game_scn.name:
            if not await self.dao.is_name_available(game_scn.name):
                raise CantEditGame(
                    player=admin,
                    text=f"cant rename game to {game_scn.name} (name is already taken)",
                )
            await self.dao.rename_game(game, game_scn.name)
            game.name = game_scn.name
        await self.dao.unlink_all(game)
        levels = []
        for number, level in enumerate(game_scn.levels):
            saved_level = await self.dao.upsert_gamed(author, level, game, number)
            await sync_files_for_level(saved_level, self.dao)
            levels.append(saved_level)
        await self.dao.commit()
        logger.warning("admin %s edited scenario of game %s", admin.id, game.id)
        return game.to_full_game(levels)


@dataclass
class AdminUploadGameFileInteractor:
    storage: FileStorage
    dao: GameFileUploader

    async def __call__(
        self,
        game_id: int,
        content: BinaryIO,
        original_filename: str,
        identity: IdentityProvider,
    ) -> hints.SavedFileMeta:
        """Upload a new media file for any game, regardless of its status.

        The file is owned by the game's author (not the acting admin) so that the
        regular author-facing editing flow keeps working with it afterwards.
        """
        admin = await identity.get_superuser()
        game = await self.dao.get_by_id(id_=game_id)
        saved = await save_file(game.author, content, original_filename, self.storage, self.dao)
        # register the file as usable in this game even before any level references it
        await self.dao.add_game_file(game.id, saved.id)
        await self.dao.commit()
        logger.warning("admin %s uploaded file %s for game %s", admin.id, saved.guid, game.id)
        return saved
