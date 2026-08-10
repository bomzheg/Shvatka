"""Interactors for a game's release — the promo published before a game.

A release is a banner — a wide title picture with a caption — followed by a
plain list of hints (the theme, a map, the rules). Writing it and announcing it
are separate steps:

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
    publisher: GameReleasePublisher

    async def __call__(
        self,
        game_id: int,
        banner: hints.PhotoHint | None,
        hints_: list[hints.AnyHint],
        identity: IdentityProvider,
    ) -> dto.GameRelease:
        author = await identity.get_required_player()
        is_superuser = await identity.is_superuser()
        if not is_superuser:
            check_allow_be_author(author)
        game = await self.dao.get_by_id(id_=game_id, author=None if is_superuser else author)
        check_can_edit_release(game, author, is_superuser)
        parts = [banner, *hints_] if banner is not None else list(hints_)
        await self.link_files(game, parts, author, is_superuser)
        await self.dao.save_release(game, banner, hints_)
        await self.dao.commit()
        release = await self.dao.get_release(game_id)
        if release is None:
            raise exceptions.SHDataBreach(
                game=game, player=author, text="release is missing right after saving"
            )
        if self.should_announce(game):
            await self.publisher.publish(game, release)
        else:
            # not this game's moment to announce — but if the release is
            # already on show somewhere, it should show what was just written
            await self.publisher.update(game, release)
        return release

    @staticmethod
    def should_announce(game: dto.Game) -> bool:
        """Whether saving this release should also put it in front of people.

        Only while the game is collecting waivers: before that the release
        waits for them to start, after that its audience is already playing.
        A release already on show is kept up to date either way.
        """
        return game.status == GameStatus.getting_waivers

    async def link_files(
        self,
        game: dto.Game,
        hints_: list[hints.AnyHint],
        author: dto.Player,
        is_superuser: bool = False,
    ) -> None:
        """Make every file the release references usable in the game.

        The files may have been uploaded straight into the release (that's how
        the bot works), so they are not registered for the game yet, and
        without that the cdn endpoint would refuse to serve the banner.
        """
        guids = [guid for hint in hints_ for guid in hint.get_guids()]
        for guid in guids:
            if is_superuser:
                # the guids of a release an admin is fixing are the author's,
                # not theirs — the ownership check is there to stop an author
                # claiming someone else's file, which is not what this is
                continue
            await self.dao.check_author_can_own_guid(author, guid)
        if guids:
            await self.dao.add_game_files(game.id, await self.dao.get_ids_by_guids(guids))


@dataclass
class DeleteGameReleaseInteractor:
    dao: GameReleaseEditor
    publisher: GameReleasePublisher

    async def __call__(self, game_id: int, identity: IdentityProvider) -> None:
        author = await identity.get_required_player()
        is_superuser = await identity.is_superuser()
        game = await self.dao.get_by_id(id_=game_id, author=None if is_superuser else author)
        check_can_edit_release(game, author, is_superuser)
        if await self.dao.get_release(game_id) is None:
            return
        await self.dao.delete_release(game)
        await self.dao.commit()
        await self.publisher.unpublish(game)
