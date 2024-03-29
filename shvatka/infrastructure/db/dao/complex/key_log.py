from dataclasses import dataclass

from shvatka.core.interfaces.dal.complex import TypedKeyGetter
from shvatka.core.models import dto
from shvatka.core.models.dto import Team, KeyTime
from shvatka.infrastructure.db.dao import KeyTimeDao, OrganizerDao


@dataclass
class TypedKeyGetterImpl(TypedKeyGetter):
    key_time: KeyTimeDao
    organizer: OrganizerDao

    async def get_typed_keys_grouped(self, game: dto.Game) -> dict[Team, list[KeyTime]]:
        return await self.key_time.get_typed_key_grouped(game=game)

    async def get_by_player(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        return await self.organizer.get_by_player(game=game, player=player)

    async def get_by_player_or_none(
        self, game: dto.Game, player: dto.Player
    ) -> dto.SecondaryOrganizer | None:
        return await self.organizer.get_by_player_or_none(game=game, player=player)
