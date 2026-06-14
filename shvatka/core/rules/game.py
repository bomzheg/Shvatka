from shvatka.core.interfaces.dal.organizer import OrgByPlayerGetter
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


async def check_can_view_scenario(
    game: dto.Game,
    player: dto.Player,
    dao: OrgByPlayerGetter,
) -> None:
    """Check the player is allowed to view the whole scenario of the game.

    Unlike :func:`check_can_read`, this also allows secondary organizers that
    were granted the ``view_scenario`` permission to read the scenario in any
    game status (not only after the game is completed).
    """
    if game.is_complete():
        return  # for completed - available for all
    if game.is_author_id(player.id):
        return
    org = await dao.get_by_player_or_none(player=player, game=game)
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
