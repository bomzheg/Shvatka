import typing
from dataclasses import dataclass

from shvatka.core.interfaces.dal.player import PlayerPromoter
from shvatka.core.players.interfaces import PlayerMerger, AdminPlayerReader, AdminEmailSetter, AdminTgChanger, \
    AdminPlayerMerger
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

    async def clean_history(self, player: dto.Player) -> None:
        return await self.dao.team_player.clean_history(player)

    async def set_history(self, history: list[dto.TeamPlayer]) -> None:
        return await self.dao.team_player.set_history(history)

    async def replace_forum_player(self, primary: dto.Player, secondary: dto.Player) -> None:
        return await self.dao.forum_user.replace_player(primary, secondary)

    async def delete_player(self, player: dto.Player) -> None:
        return await self.dao.player.delete(player)

    async def get_email_by_player_id(self, player_id: int) -> dto.EmailAccount | None:
        return await self.dao.email.get_by_player_id(player_id)

    async def commit(self) -> None:
        return await self.dao.commit()


@dataclass
class AdminPlayerMergerImpl(PlayerMergerImpl, AdminPlayerMerger):
    async def get_by_id(self, id_: int) -> dto.Player:
        return await self.dao.player.get_by_id(id_)


@dataclass
class AdminPlayerReaderImpl(AdminPlayerReader):
    dao: "HolderDao"

    async def get_by_id(self, id_: int) -> dto.Player:
        return await self.dao.player.get_by_id(id_)

    async def get_email_by_player_id(self, player_id: int) -> dto.EmailAccount | None:
        return await self.dao.email.get_by_player_id(player_id)


@dataclass
class AdminEmailSetterImpl(AdminEmailSetter):
    dao: "HolderDao"

    async def get_by_id(self, id_: int) -> dto.Player:
        return await self.dao.player.get_by_id(id_)

    async def get_by_email(self, email: str) -> dto.EmailAccount | None:
        return await self.dao.email.get_by_email(email)

    async def set_player_email(
        self, player_id: int, email: str, is_verified: bool
    ) -> dto.EmailAccount:
        return await self.dao.email.set_player_email(player_id, email, is_verified)

    async def commit(self) -> None:
        return await self.dao.commit()


@dataclass
class AdminTgChangerImpl(AdminTgChanger):
    dao: "HolderDao"

    async def upsert_user(self, user: dto.User) -> dto.User:
        return await self.dao.user.upsert_user(user)

    async def get_by_id(self, id_: int) -> dto.Player:
        return await self.dao.player.get_by_id(id_)

    async def get_by_user_id(self, user_id: int) -> dto.Player:
        return await self.dao.player.get_by_user_id(user_id)

    async def unlink_user(self, player: dto.Player) -> None:
        return await self.dao.player.unlink_user(player)

    async def link_user(self, player: dto.Player, user: dto.User) -> None:
        return await self.dao.player.link_user(player, user)

    async def get_email_by_player_id(self, player_id: int) -> dto.EmailAccount | None:
        return await self.dao.email.get_by_player_id(player_id)

    async def commit(self) -> None:
        return await self.dao.commit()
