from shvatka.core.models import dto
from .game import check_game_editable
from shvatka.core.utils.exceptions import NotAuthorizedForEdit, SHDataBreach


def check_is_author(level: dto.Level, player: dto.Player):
    if level.author.id != player.id:
        raise NotAuthorizedForEdit(
            permission_name="game_edit",
            player=player,
            level=level,
        )


def check_is_org(level: dto.Level, org: dto.SecondaryOrganizer):
    if level.game_id != org.game.id or org.deleted:
        raise NotAuthorizedForEdit(
            permission_name="game_edit",
            player=org.player,
            level=level,
        )


def check_can_edit(level: dto.Level, author: dto.Player, game: dto.Game | None = None) -> None:
    check_is_author(level, author)
    # TODO check game status


def check_can_link_to_game(game: dto.Game, level: dto.Level, author: dto.Player | None = None):
    if level.game_id is not None and level.game_id != game.id:
        raise SHDataBreach(
            player=author,
            notify_user=f"уровень {level.name_id} привязан к другой игре",
        )
    check_game_editable(game)
