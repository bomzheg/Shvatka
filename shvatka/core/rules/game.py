from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums.org_permission import OrgPermission
from shvatka.core.utils.exceptions import NotAuthorizedForEdit, CantEditGame


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


def check_game_editable(game: dto.Game):
    if not game.can_be_edited:
        raise CantEditGame(
            game=game, player=game.author, notify_user="Невозможно изменить игру после начала"
        )


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
