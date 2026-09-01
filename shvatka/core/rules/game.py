from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums.game_status import (
    ADMIN_MANAGEABLE_STATUSES,
    PLAYED_STATUSES,
    REWOUND_STATUSES,
    GameStatus,
)
from shvatka.core.models.enums.org_permission import OrgPermission
from shvatka.core.utils.exceptions import (
    CantEditGame,
    GameNotFound,
    GameStatusError,
    NotAuthorizedForEdit,
)


def check_can_read(game: dto.Game, player: dto.Player):
    if game.is_complete():
        return  # for completed - available for all
    if not game.is_author_id(player.id):
        raise NotAuthorizedForEdit(
            permission_name="game_edit",
            player=player,
            game=game,
        )


async def check_can_view_scenario(game: dto.Game, identity: IdentityProvider) -> None:
    """Who may read a game's scenario: everyone once it is complete, else the
    author and the orgs given ``view_scenario``.

    Admin rights are deliberately not on that list. An admin edits a game only
    once it is complete (see :mod:`shvatka.core.games.admin_interactors`), and
    a complete game is public anyway — so being a superuser never opens a
    scenario still being written, however the game is addressed.
    """
    player = await identity.get_required_player()
    if game.is_complete():
        return  # for completed - available for all
    if game.is_author_id(player.id):
        return
    org = await identity.get_org(game=game)
    if org is not None and not org.deleted and org.view_scenario:
        return
    raise NotAuthorizedForEdit(
        permission_name=OrgPermission.view_scenario.name,
        player=player,
        game=game,
    )


def check_admin_can_manage_game(game: dto.Game) -> None:
    """Whether the admin panel may act on the game at all.

    An admin sees a game only once it stops being a draft: while it collects
    waivers, runs, is finished or is complete. A game in ``underconstruction``
    or ``ready`` is its author's alone — reported as not found, the same way
    the scenario endpoints hide it, so an admin cannot even tell it exists.

    What the admin may then do with it is its *status*, nothing else: the
    content of a game that is not complete stays closed to admins (see
    :func:`check_can_view_scenario`).
    """
    if game.status not in ADMIN_MANAGEABLE_STATUSES:
        raise GameNotFound(game=game)


def check_can_purge_game_runtime(game: dto.Game, status: GameStatus) -> None:
    """Whether the run of ``game`` may be swept as it moves to ``status``.

    Only on the way back: a game that was played (``started``, ``finished``,
    ``complete``) moving to a status before its run (``getting_waivers``,
    ``ready``, ``underconstruction``). That move is the admin declaring the run
    never happened — a false start, a game opened on the wrong evening — and
    the level times, keys, events and timers it left behind are what would
    otherwise make the game unplayable a second time.

    Any other move keeps them: a game that is merely being renumbered or
    completed still owns its history, and nothing about the panel should be
    able to erase the history of a game that is going on.
    """
    if game.status not in PLAYED_STATUSES or status not in REWOUND_STATUSES:
        raise GameStatusError(
            game_status=game.status.name,
            game=game,
            text=(
                f"cant purge the run of a game moving from " f"{game.status.name} to {status.name}"
            ),
            notify_user=(
                "Очистить ход игры можно только возвращая сыгранную игру "
                "к сбору вейверов или в черновики"
            ),
        )


def check_game_editable(game: dto.Game):
    if not game.can_be_edited:
        raise CantEditGame(
            game=game, player=game.author, notify_user="Невозможно изменить игру после начала"
        )


def check_game_name(name: str, player: dto.Player) -> None:
    """Whether a string may be a game's name.

    Only emptiness is refused here — whether the name is *free* is a question
    for the storage, asked by the caller that writes it.
    """
    if not name.strip():
        raise CantEditGame(
            player=player,
            text="game name can not be empty",
            notify_user="Название игры не может быть пустым",
        )


def check_can_add_file(game: dto.Game, player: dto.Player, is_superuser: bool = False) -> None:
    """Whether a file may still be added to the game.

    Later than :func:`check_game_editable`: the scenario freezes when the game
    starts, but the release does not, and its banner has to be uploaded
    somewhere. A file nothing references is inert — what it may be used for is
    guarded where it is used — so adding one need only be allowed as widely as
    the widest thing that can still reference it, which is the release.

    An admin may rewrite any release, a complete game's included, so an admin
    may bring a banner for it. Callers that let an author *change* an existing
    file rather than add one leave ``is_superuser`` alone: that is the author's
    to do.
    """
    check_can_edit_release(game, player, is_superuser)


def check_can_edit_release(game: dto.Game, player: dto.Player, is_superuser: bool = False) -> None:
    """A release can be rewritten up to and including a finished game.

    Unlike the scenario it stays editable while the game runs — it is promo,
    not part of the play. Once the game is complete it is history, and only an
    admin may still touch it.
    """
    if is_superuser:
        return
    if game.is_complete():
        raise NotAuthorizedForEdit(
            permission_name="game_release_edit",
            player=player,
            game=game,
            notify_user="Игра уже завершена, релиз может изменить только администратор",
        )
    if not game.is_author_id(player.id):
        raise NotAuthorizedForEdit(
            permission_name="game_release_edit",
            player=player,
            game=game,
        )
