import typing
from dataclasses import dataclass

from shvatka.core.interfaces.dal.player import PlayerPromoter, PlayerMerger
from shvatka.core.models import dto

if typing.TYPE_CHECKING:
    from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class PlayerPromoterImpl(PlayerPromoter):
    dao: "HolderDao"

    async def promote(self, actor: dto.Player, target: dto.Player) -> None:
        return await self.dao.player.promote(actor, target)

    async def get_by_id(self, id_: int) -> dto.Player:
        return await self.dao.player.get_by_id(id_)

    async def commit(self) -> None:
        return await self.dao.player.commit()

    async def get_invite(self, token: str) -> dict:
        return await self.dao.secure_invite.get_invite(token)

    async def remove_invite(self, token: str) -> None:
        return await self.dao.secure_invite.remove_invite(token)


@dataclass
class PlayerMergerImpl(PlayerMerger):
    dao: "HolderDao"

    async def replace_games_author(self, primary: dto.Player, secondary: dto.Player) -> None:
        return await self.dao.game.transfer_all(primary, secondary)

    async def replace_levels_author(self, primary: dto.Player, secondary: dto.Player) -> None:
        return await self.dao.level.transfer_all(primary, secondary)

    async def replace_file_info(self, primary: dto.Player, secondary: dto.Player) -> None:
        return await self.dao.file_info.transfer_all(primary, secondary)

    async def replace_player_keys(self, primary: dto.Player, secondary: dto.Player) -> None:
        return await self.dao.key_time.replace_player_keys(primary, secondary)

    async def replace_player_org(self, primary: dto.Player, secondary: dto.Player) -> None:
        return await self.dao.key_time.replace_player_keys(primary, secondary)

    async def replace_player_waiver(self, primary: dto.Player, secondary: dto.Player) -> None:
        return await self.dao.waiver.replace_all_waivers(primary, secondary)

    async def get_player_teams_history(self, player: dto.Player) -> list[dto.TeamPlayer]:
        return await self.dao.team_player.get_history(player)

    async def commit(self) -> None:
        return await self.dao.commit()
