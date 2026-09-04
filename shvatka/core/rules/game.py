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
    if game.status not in ADMIN_MANAGEABLE_STATUSES:
        raise GameNotFound(game=game)


def check_can_purge_game_runtime(game: dto.Game, status: GameStatus) -> None:
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
    if not name.strip():
        raise CantEditGame(
            player=player,
            text="game name can not be empty",
            notify_user="Название игры не может быть пустым",
        )


def check_can_add_file(game: dto.Game, player: dto.Player, is_superuser: bool = False) -> None:
    check_can_edit_release(game, player, is_superuser)


def check_can_edit_release(game: dto.Game, player: dto.Player, is_superuser: bool = False) -> None:
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
