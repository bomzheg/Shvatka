from datetime import date

from shvatka.core.models import dto
from shvatka.core.season import dto as season_dto


def make_player(id_: int, *, can_be_author: bool = True) -> dto.Player:
    return dto.Player(id=id_, can_be_author=can_be_author, is_dummy=False, username=f"player{id_}")


def make_team(id_: int, captain: dto.Player | None) -> dto.Team:
    return dto.Team(id=id_, name=f"team{id_}", captain=captain, is_dummy=False, description=None)


def make_slot(
    id_: int,
    day: date,
    *,
    owner: dto.Player | None = None,
    game: season_dto.LinkedGame | None = None,
) -> season_dto.Slot:
    return season_dto.Slot(
        id=id_,
        season_id=1,
        date=day,
        owner=owner,
        author_kind=season_dto.SlotAuthorKind.player if owner else None,
        game=game,
    )
