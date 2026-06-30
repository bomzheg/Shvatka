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

from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.dal.complex import GameCompleter, GameScenarioEditor
from shvatka.core.interfaces.dal.game import (
    GameAuthorsFinder,
    GameByIdGetter,
    GameCreator,
    GameFileUploader,
    GameStartPlanner,
    WaiverStarter,
)
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import hints
from shvatka.core.players.player import check_allow_be_author
from shvatka.core.rules.game import check_game_editable
from shvatka.core.services.game import (
    cancel_planed_start,
    complete_game,
    create_game,
    get_authors_games,
    get_full_game,
    plain_start,
    start_waivers,
    update_game_scenario,
)
from shvatka.core.services.scenario.files import save_file
from shvatka.core.utils import exceptions

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

    async def __call__(
        self, game_id: int, start_at: datetime | None, identity: IdentityProvider
    ) -> dto.Game:
        author = await identity.get_required_player()
        game = await self.getter.get_by_id(id_=game_id, author=author)
        if start_at is None:
            await cancel_planed_start(game, author, self.scheduler, self.dao)
        else:
            await plain_start(game, author, start_at, self.dao, self.scheduler)
        return game


@dataclass
class ChangeGameStatusInteractor:
    getter: GameByIdGetter
    waiver_starter: WaiverStarter
    completer: GameCompleter

    async def __call__(
        self, game_id: int, status: enums.GameStatus, identity: IdentityProvider
    ) -> dto.Game:
        author = await identity.get_required_player()
        game = await self.getter.get_by_id(id_=game_id, author=author)
        if status == enums.GameStatus.getting_waivers:
            await start_waivers(game, author, self.waiver_starter)
        elif status == enums.GameStatus.complete:
            await complete_game(game, self.completer)
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
    ) -> hints.SavedFileMeta:
        author = await identity.get_required_player()
        check_allow_be_author(author)
        game = await self.dao.get_by_id(id_=game_id, author=author)
        check_game_editable(game)
        saved = await save_file(author, content, original_filename, self.storage, self.dao)
        # the file is uploaded for later use in this game even though it is not yet
        # assigned to any level, so register it as usable in the game.
        await self.dao.add_game_file(game.id, saved.id)
        await self.dao.commit()
        return saved
