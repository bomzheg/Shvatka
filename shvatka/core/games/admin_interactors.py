"""Interactors backing admin edits of **completed** games.

Unlike the author-facing editor interactors in :mod:`editor_interactors`, these
take the acting user via an ``IdentityProvider`` and authorise through
``identity.get_superuser()``. They skip the game-ownership check and the
``check_game_editable`` guard (which forbids editing a finished game), so an
admin may fix up an already completed game — edit its scenario, reassign its
author and upload new media files.

Admin access is limited to completed games: any game in another status is
treated as not found (an admin cannot even see it here).
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
from shvatka.core.services.scenario.files import save_file, sync_files_for_level
from shvatka.core.services.scenario.game_ops import parse_uploaded_game
from shvatka.core.utils.exceptions import CantEditGame, GameNotFound, SHDataBreach

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
        """Replace the whole scenario of a completed game.

        Files are expected to be already uploaded (only their guids are
        referenced). When ``new_author_id`` is given, the game (and the levels
        upserted here) is reassigned to that player first. A game that is not
        completed is reported as not found.
        """
        admin = await identity.get_superuser()
        game_scn = parse_uploaded_game(scn.RawGameScenario(scn=raw_scn, files={}), self.retort)
        game = await self.dao.get_by_id(id_=game_id)
        if not game.is_complete():
            raise GameNotFound(game=game)
        if new_author_id is not None and new_author_id != game.author.id:
            new_author = await self.dao.get_player_by_id(new_author_id)
            # move the game and its level rows together so authorship stays consistent
            await self.dao.transfer(game, new_author)
            await self.dao.transfer_levels(game, new_author)
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
        # detach all current levels, then re-attach exactly the ones the new scenario
        # keeps (matched by author + name_id, so the same rows are reused). upsert
        # without a game and link_to_game do not run the editability guard, so a
        # completed game can be edited without faking its status.
        await self.dao.unlink_all(game)
        levels = []
        for level in game_scn.levels:
            saved = await self.dao.upsert(author, level)
            if saved.game_id is not None:
                # the level is attached to another game — never steal it
                raise SHDataBreach(
                    player=admin,
                    notify_user=f"уровень {saved.name_id} привязан к другой игре",
                )
            linked = await self.dao.link_to_game(saved, game)
            await sync_files_for_level(linked, self.dao)
            levels.append(linked)
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
        """Upload a new media file for a completed game.

        The file is owned by the game's author (not the acting admin) so that the
        regular author-facing editing flow keeps working with it afterwards. A
        game that is not completed is reported as not found.
        """
        admin = await identity.get_superuser()
        game = await self.dao.get_by_id(id_=game_id)
        if not game.is_complete():
            # admins operate on completed games only; anything else is hidden
            raise GameNotFound(game=game)
        saved = await save_file(game.author, content, original_filename, self.storage, self.dao)
        # register the file as usable in this game even before any level references it
        await self.dao.add_game_file(game.id, saved.id)
        await self.dao.commit()
        logger.warning("admin %s uploaded file %s for game %s", admin.id, saved.guid, game.id)
        return saved
