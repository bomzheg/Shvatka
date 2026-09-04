"""Interactors backing admin edits of **completed** games.

Unlike the author-facing editor interactors in :mod:`editor_interactors`, these
take the acting user via an ``IdentityProvider`` and authorise through
``identity.get_superuser()``. They skip the game-ownership check and the
``check_game_editable`` guard (which forbids editing a finished game), so an
admin may fix up an already completed game — edit its scenario, reassign its
author and upload new media files.

Admin access to a game's *content* is limited to completed games — a
completed game is public anyway — so any game in another status is treated as
not found there (an admin cannot even see it exists).

A game's *status* is a different matter: the panel may walk a game that
collects waivers, runs, is finished or is complete to another status (see
:class:`AdminChangeGameStatusInteractor`), without ever reading a level, a
hint or a file of it. Games still being written stay invisible even to that.
Rewinding a played game may take the run with it — the level times, keys,
events and timers of a false start — which is a delete and never a read.

The same line runs through the one thing the panel may do to a game that is
being *played* — resending a level's messages to a team that lost them (see
:class:`AdminResendCurrentLevelInteractor`). The admin presses the button;
the puzzle and the hints go from the engine straight to the team, and neither
they nor the team's position in the game ever pass through the panel.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import BinaryIO

from adaptix import Retort

from shvatka.core.games.adapters import (
    AdminGameScenarioEditor,
    AdminGameStatusChanger,
    AdminLevelResender,
)
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.dal.game import GameFileUploader
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto
from shvatka.core.models.dto import hints, scn
from shvatka.core.models.enums import GameStatus
from shvatka.core.models.enums.game_status import ACTIVE_STATUSES, ADMIN_MANAGEABLE_STATUSES
from shvatka.core.rules.game import check_admin_can_manage_game, check_can_purge_game_runtime
from shvatka.core.services.game import check_no_other_game_active, complete_game
from shvatka.core.services.scenario.files import save_file, sync_files_for_level
from shvatka.core.services.scenario.game_ops import parse_uploaded_game
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.exceptions import (
    CantEditGame,
    GameNotFound,
    GameStatusError,
    SHDataBreach,
    TeamCurrentLevelNotFound,
    TeamError,
)
from shvatka.core.views.game import (
    AnyViewTask,
    SendHint,
    SendPuzzle,
    ShowTasks,
    ViewSender,
)

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


@dataclass
class AdminGamesListInteractor:
    """The games the admin panel may act on — status and nothing more.

    Only the ones an admin is allowed to see: active (collecting waivers,
    running, finished) and complete. A game still being written belongs to its
    author and does not show up here.
    """

    dao: AdminGameStatusChanger

    async def __call__(self, identity: IdentityProvider) -> list[dto.Game]:
        await identity.get_superuser()
        return await self.dao.get_by_statuses(ADMIN_MANAGEABLE_STATUSES)


@dataclass
class AdminChangeGameStatusInteractor:
    """Move a game to another status over the author's head.

    Only the status changes — nothing here reads or writes the game's content.
    Two things ride along, because leaving them behind would undo the move: a
    game leaving the active statuses loses its planned start, and a game moving
    to ``complete`` goes through the author's own domain service.

    With ``purge_runtime`` the move also sweeps the run the false start left
    behind. Allowed only on the way back — see
    :func:`~shvatka.core.rules.game.check_can_purge_game_runtime` — and never
    touching the waivers. SHEP-0013.
    """

    dao: AdminGameStatusChanger
    scheduler: Scheduler

    async def __call__(
        self,
        game_id: int,
        status: GameStatus,
        identity: IdentityProvider,
        purge_runtime: bool = False,
    ) -> dto.Game:
        admin = await identity.get_superuser()
        game = await self.dao.get_by_id(id_=game_id)
        check_admin_can_manage_game(game)
        if purge_runtime:
            # refuse before anything is written: an admin who ticked the box on
            # a move that keeps the run must be told, not quietly obeyed by half
            check_can_purge_game_runtime(game, status)
        if status == game.status:
            return game
        if status in ACTIVE_STATUSES:
            # only one game may be active at a time — that invariant is the
            # engine's, and an admin repairing one game must not break it
            await check_no_other_game_active(self.dao, game)
        if status == GameStatus.complete:
            await complete_game(game, self.dao)
        else:
            await self.dao.set_status(game, status)
            if status not in ACTIVE_STATUSES:
                await self._cancel_planned_start(game)
            if purge_runtime:
                await self._purge_runtime(game, admin)
            await self.dao.commit()
        logger.warning("admin %s changed status of game %s to %s", admin.id, game.id, status.name)
        return game

    async def _purge_runtime(self, game: dto.Game, admin: dto.Player) -> None:
        """Erase what playing the game produced, deepest reference first.

        ``log_keys`` and ``timers_log`` point at both ``event_log`` and
        ``levels_times``, and ``event_log`` points at ``levels_times`` — so the
        order is fixed, and ``timers_log`` (which has no game of its own) is
        addressed through the level time ids read before anything is dropped.
        """
        level_time_ids = await self.dao.get_level_time_ids(game)
        await self.dao.delete_timers(level_time_ids)
        await self.dao.delete_typed_keys(game)
        await self.dao.delete_events(game)
        await self.dao.delete_level_times(game)
        logger.warning(
            "admin %s purged the run of game %s (%s level times)",
            admin.id,
            game.id,
            len(level_time_ids),
        )

    async def _cancel_planned_start(self, game: dto.Game) -> None:
        if game.start_at is None:
            return
        await self.dao.cancel_start(game)
        game.start_at = None
        await self.scheduler.cancel_scheduled_game(game)


@dataclass
class AdminResendCurrentLevelInteractor:
    """Send a running level's messages to a team again, without reading them.

    Out goes what the team is entitled to have right now: the puzzle of the
    level it is on and every hint whose time has come. It goes from the engine
    to the views directly, so the admin sends the hints without seeing one.

    The answer is the teams the request covered and nothing else — not the
    level any of them is on, not whether it is still playing. A team past the
    last level is answered for like the rest and simply has nothing to resend,
    so the panel cannot read a team's progress off the difference.
    """

    dao: AdminLevelResender
    sender: ViewSender
    current_game: CurrentGameProvider

    async def __call__(
        self, identity: IdentityProvider, team_id: int | None = None
    ) -> list[dto.Team]:
        admin = await identity.get_superuser()
        game = await self.current_game.get_required_full_game()
        if not game.is_started():
            # there is nothing to resend before the first puzzle went out
            raise GameStatusError(
                game_status=game.status.name,
                game=game,
                text="cant resend level messages of a game that is not started",
                notify_user="Переотправить сообщения уровня можно только в идущей игре",
            )
        teams = await self._resolve_teams(game, team_id)
        tasks = ShowTasks()
        for team in teams:
            tasks.view.extend(await self._level_messages(team, game))
        await self.sender.show_later(tasks)
        logger.warning(
            "admin %s resent level messages of game %s to %s team(s)",
            admin.id,
            game.id,
            len(teams),
        )
        return teams

    async def _resolve_teams(self, game: dto.FullGame, team_id: int | None) -> list[dto.Team]:
        """The teams to resend to — always taken from the ones playing.

        A team that did not sign up for this game has no level to be sent, so
        naming one is a mistake rather than a way to find out anything: the
        answer is the same refusal whether the team exists or not.
        """
        played = list(await self.dao.get_played_teams(game))
        if team_id is None:
            return played
        for team in played:
            if team.id == team_id:
                return [team]
        raise TeamError(
            team_id=team_id,
            game=game,
            text=f"team {team_id} does not play the current game",
            notify_user="Эта команда не играет в текущей игре",
        )

    async def _level_messages(self, team: dto.Team, game: dto.FullGame) -> list[AnyViewTask]:
        try:
            level_time = await self.dao.get_current_level_time(team, game)
        except TeamCurrentLevelNotFound:
            # played teams normally have one; a team without it has nothing to lose
            return []
        if level_time.has_finished(game):
            return []
        level = game.levels[level_time.level_number]
        shown = level.get_hints_for_timedelta(datetime.now(tz=tz_utc) - level_time.start_at)
        # hint #0 is the puzzle itself, the rest are the hints already released
        tasks: list[AnyViewTask] = [SendPuzzle(team=team, level=level)]
        tasks.extend(
            SendHint(team=team, hint_number=number, level=level) for number in range(1, len(shown))
        )
        return tasks
