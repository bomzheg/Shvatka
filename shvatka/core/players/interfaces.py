from typing import Protocol

from shvatka.core.interfaces.dal.base import Committer
from shvatka.core.interfaces.dal.file_info import FileInfoMerger
from shvatka.core.interfaces.dal.game import GameAuthorMerger
from shvatka.core.interfaces.dal.key_log import PlayerKeysMerger
from shvatka.core.interfaces.dal.level import LevelAuthorMerger
from shvatka.core.interfaces.dal.organizer import PlayerOrgMerger
from shvatka.core.interfaces.dal.player import (
    TeamPlayerHistoryGetter,
    TeamPlayerHistoryCleaner,
    TeamPlayerHistorySetter,
    ForumPlayerMerger,
    PlayerDeleter,
    WaiverPlayerMerger,
    PlayerByIdGetter,
    PlayerByUserIdGetter,
)
from shvatka.core.interfaces.dal.user import UserUpserter
from shvatka.core.models import dto


class UserPasswordSetter(Committer, Protocol):
    async def set_password(self, player: dto.Player, hashed_password: str):
        raise NotImplementedError


class PlayerUsernameChanger(Committer, Protocol):
    async def is_username_occupied(self, username: str) -> bool:
        raise NotImplementedError

    async def set_username(self, player: dto.Player, username: str) -> None:
        raise NotImplementedError


class PlayerSearcher(Protocol):
    async def search_players(
        self,
        *,
        username: str | None = None,
        name: str | None = None,
        active: bool = True,
        archive: bool = False,
        can_be_author: bool | None = None,
    ) -> list[dto.Player]:
        raise NotImplementedError


class PlayerWithStatGetter(Protocol):
    async def get_player_with_stat(self, id_: int) -> dto.PlayerWithStat:
        raise NotImplementedError


class PlayedGamesByPlayerGetter(Protocol):
    async def get_played_games(self, player: dto.Player) -> list[dto.Game]:
        raise NotImplementedError


class EmailByPlayerIdReader(Protocol):
    async def get_email_by_player_id(self, player_id: int) -> dto.EmailAccount | None:
        raise NotImplementedError


class EmailMerger(EmailByPlayerIdReader, Protocol):
    async def delete_email(self, email: dto.EmailAccount) -> None:
        raise NotImplementedError

    async def replace_email_player(self, email: dto.EmailAccount, player_id: int) -> None:
        raise NotImplementedError


class PlayerMerger(
    GameAuthorMerger,
    LevelAuthorMerger,
    PlayerKeysMerger,
    PlayerOrgMerger,
    TeamPlayerHistoryGetter,
    TeamPlayerHistoryCleaner,
    TeamPlayerHistorySetter,
    ForumPlayerMerger,
    PlayerDeleter,
    WaiverPlayerMerger,
    FileInfoMerger,
    EmailMerger,
    Committer,
    Protocol,
):
    pass


class AdminPlayerReader(PlayerByIdGetter, EmailByPlayerIdReader, Protocol):
    """Load a player by id together with their email account."""


class AdminEmailSetter(PlayerByIdGetter, Committer, Protocol):
    async def get_by_email(self, email: str) -> dto.EmailAccount | None:
        raise NotImplementedError

    async def set_player_email(
        self, player_id: int, email: str, is_verified: bool
    ) -> dto.EmailAccount:
        raise NotImplementedError


class AdminTgChanger(
    UserUpserter, PlayerByIdGetter, PlayerByUserIdGetter, EmailByPlayerIdReader, Protocol
):
    async def unlink_user(self, player: dto.Player) -> None:
        raise NotImplementedError

    async def link_user(self, player: dto.Player, user: dto.User) -> None:
        raise NotImplementedError


class AdminPlayerMerger(PlayerMerger, PlayerByIdGetter, Protocol):
    """Merge one player into another, plus load both by id."""
