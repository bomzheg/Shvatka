import typing
from dataclasses import dataclass

from shvatka.core.games.adapters import GameKeysReader
from shvatka.core.interfaces.dal.complex import TypedKeyGetter
from shvatka.core.models import dto
from shvatka.core.models.dto import Team, KeyTime

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class TypedKeyGetterImpl(TypedKeyGetter):
    dao: "HolderDao"

    async def get_typed_keys_grouped(self, game: dto.Game) -> dict[Team, list[KeyTime]]:
        return await self.dao.key_time.get_typed_key_grouped(game=game)

    async def get_by_player(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        return await self.dao.organizer.get_by_player(game=game, player=player)

    async def get_by_player_or_none(
        self, game: dto.Game, player: dto.Player
    ) -> dto.SecondaryOrganizer | None:
        return await self.dao.organizer.get_by_player_or_none(game=game, player=player)


class GameKeysReaderImpl(GameKeysReader):
    def __init__(self, dao: "HolderDao"):
        self.dao = dao

    async def get_typed_keys_grouped(self, game: dto.Game) -> dict[Team, list[KeyTime]]:
        return await self.dao.key_time.get_typed_key_grouped(game=game)

    async def get_by_player(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        return await self.dao.organizer.get_by_player(game=game, player=player)

    async def get_by_player_or_none(
        self, game: dto.Game, player: dto.Player
    ) -> dto.SecondaryOrganizer | None:
        return await self.dao.organizer.get_by_player_or_none(game=game, player=player)

    async def get_by_id(self, id_: int, author: dto.Player | None = None) -> dto.Game:
        return await self.dao.game.get_by_id(id_, author)

    async def get_full(self, id_: int) -> dto.FullGame:
        return await self.dao.game.get_full(id_)

    async def get_by_user(self, user: dto.User) -> dto.Player:
        return await self.dao.player.get_by_user(user)
