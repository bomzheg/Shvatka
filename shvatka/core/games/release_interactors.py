"""Interactors for a game's release — the promo published before a game.

A release is a plain list of hints (banner, text about the theme, a map)
attached to a game. Writing it and announcing it are separate steps:

* it can be written and rewritten at any time, up to and including a finished
  game (a complete one is history — only an admin may still touch it);
* it goes to the announcements channel when the game starts collecting waivers
  — or right away if it is written while the game is already collecting them;
* a release written after the game has started is only stored, never posted:
  the audience it was meant for is already playing;
* editing an already posted release edits those channel messages in place.

A release is optional: nothing in the game flow requires one.
"""

import logging
from dataclasses import dataclass

from shvatka.core.games.adapters import GameReleaseEditor, GameReleaseReader
from shvatka.core.interfaces.dal.game import GameReleasePostSaver
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.dto import hints
from shvatka.core.models.enums import GameStatus
from shvatka.core.players.player import check_allow_be_author
from shvatka.core.rules.game import check_can_edit_release
from shvatka.core.utils import exceptions
from shvatka.core.views.game import GameReleasePublisher

logger = logging.getLogger(__name__)


@dataclass
class GameReleaseAnnouncer:
    """Puts the release in the channel and remembers where it landed.

    Posts it the first time and edits those messages afterwards — the
    publisher decides which of the two it can do. An edge that has no channel
    to post to (or a game whose release was never posted) simply changes
    nothing.
    """

    dao: GameReleasePostSaver
    publisher: GameReleasePublisher

    async def announce(self, game: dto.Game) -> None:
        release = await self.dao.get_release(game.id)
        if release is None:
            return
        post = await self.publisher.publish(game, release)
        if post == release.post:
            return
        await self.dao.save_release_post(game, post)
        await self.dao.commit()

    async def revoke(self, game: dto.Game, release: dto.GameRelease) -> None:
        if release.post is None:
            return
        await self.publisher.unpublish(game, release.post)


@dataclass
class GetGameReleaseInteractor:
    dao: GameReleaseReader

    async def __call__(self, game_id: int) -> dto.GameRelease | None:
        """The game's release, or ``None`` when it has none.

        Readable by anyone — a release is promo, shown to guests too.
        """
        return await self.dao.get_release(game_id)


@dataclass
class SaveGameReleaseInteractor:
    dao: GameReleaseEditor
    announcer: GameReleaseAnnouncer

    async def __call__(
        self, game_id: int, hints_: list[hints.AnyHint], identity: IdentityProvider
    ) -> dto.GameRelease:
        author = await identity.get_required_player()
        is_superuser = await identity.is_superuser()
        if not is_superuser:
            check_allow_be_author(author)
        game = await self.dao.get_by_id(id_=game_id, author=None if is_superuser else author)
        check_can_edit_release(game, author, is_superuser)
        await self.link_files(game, hints_, author)
        stored = await self.dao.get_release(game_id)
        await self.dao.save_release(game, hints_)
        await self.dao.commit()
        if self.should_announce(game, stored):
            await self.announcer.announce(game)
        release = await self.dao.get_release(game_id)
        if release is None:
            raise exceptions.SHDataBreach(
                game=game, player=author, text="release is missing right after saving"
            )
        return release

    @staticmethod
    def should_announce(game: dto.Game, stored: dto.GameRelease | None) -> bool:
        """Whether saving this release should also reach the channel.

        An already posted release is kept in sync whatever the game's status.
        A new one only goes out while the game is collecting waivers — before
        that it waits for the waivers to start, after that its audience is
        already playing.
        """
        if stored is not None and stored.is_published:
            return True
        return game.status == GameStatus.getting_waivers

    async def link_files(
        self, game: dto.Game, hints_: list[hints.AnyHint], author: dto.Player
    ) -> None:
        """Make every file the release references usable in the game.

        The files may have been uploaded straight into the release (that's how
        the bot works), so they are not registered for the game yet, and
        without that the cdn endpoint would refuse to serve the banner.
        """
        guids = [guid for hint in hints_ for guid in hint.get_guids()]
        for guid in guids:
            await self.dao.check_author_can_own_guid(author, guid)
        if guids:
            await self.dao.add_game_files(game.id, await self.dao.get_ids_by_guids(guids))


@dataclass
class DeleteGameReleaseInteractor:
    dao: GameReleaseEditor
    announcer: GameReleaseAnnouncer

    async def __call__(self, game_id: int, identity: IdentityProvider) -> None:
        author = await identity.get_required_player()
        is_superuser = await identity.is_superuser()
        game = await self.dao.get_by_id(id_=game_id, author=None if is_superuser else author)
        check_can_edit_release(game, author, is_superuser)
        release = await self.dao.get_release(game_id)
        if release is None:
            return
        await self.dao.delete_release(game)
        await self.dao.commit()
        await self.announcer.revoke(game, release)
