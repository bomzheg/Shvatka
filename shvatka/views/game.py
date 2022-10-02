from typing import Protocol, Iterable

from shvatka.models import dto


class GameViewPreparer(Protocol):
    async def prepare_game_view(
        self, game: dto.Game, teams: Iterable[dto.Team], orgs: Iterable[dto.Organizer],
    ):
        pass
