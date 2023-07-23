from shvatka.core.models import dto
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


def check_game_editable(game: dto.Game):
    if not game.can_be_edited:
        raise CantEditGame(
            game=game, player=game.author, notify_user="Невозможно изменить игру после начала"
        )
