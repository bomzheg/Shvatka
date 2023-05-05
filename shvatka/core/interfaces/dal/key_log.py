from typing import Protocol

from shvatka.core.interfaces.dal.organizer import OrgByPlayerGetter
from shvatka.core.models import dto


class TypedKeyGetter(OrgByPlayerGetter, Protocol):
    async def get_typed_keys(self, game: dto.Game) -> list[dto.KeyTime]:
        raise NotImplementedError


class TeamKeysMerger(Protocol):
    async def replace_team_keys(self, primary: dto.Team, secondary: dto.Team):
        raise NotImplementedError


class PlayerKeysMerger(Protocol):
    async def replace_player_keys(self, primary: dto.Player, secondary: dto.Player):
        raise NotImplementedError
