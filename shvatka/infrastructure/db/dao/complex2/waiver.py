from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.exc import NoResultFound

from shvatka.core.models import dto
from shvatka.core.models.enums import Played
from shvatka.core.utils import exceptions
from shvatka.core.waiver.adapters import (
    WaiverVoteAdder,
    WaiverVoteGetter,
    PollDraftsReader,
    PollVoteRemover,
    AdminPollReader,
    AdminGameWaiversReader,
)
from shvatka.infrastructure.db.dao.holder import HolderDao


@dataclass
class WaiverVoteAdderImpl(WaiverVoteAdder):
    dao: HolderDao

    async def is_excluded(
        self,
        game: dto.Game,
        player: dto.Player,
        team: dto.Team,
    ) -> bool:
        return await self.dao.waiver.is_excluded(game, player, team)

    async def add_player_vote(self, team_id: int, player_id: int, vote_var: str) -> None:
        return await self.dao.poll.add_player_vote(team_id, player_id, vote_var)

    async def get_team_player(self, player: dto.Player) -> dto.TeamPlayer:
        return await self.dao.team_player.get_team_player(player)


@dataclass
class WaiverVoteGetterImpl(WaiverVoteGetter):
    dao: HolderDao

    async def get_dict_player_vote(self, team_id: int) -> dict[int, Played]:
        return await self.dao.poll.get_dict_player_vote(team_id)

    async def get_by_ids_with_user_and_pit(self, ids: Iterable[int]) -> list[dto.VotedPlayer]:
        return await self.dao.player.get_by_ids_with_user_and_pit(ids)


@dataclass
class PollDraftsReaderImpl(PollDraftsReader):
    dao: HolderDao

    async def get_polled_teams(self) -> list[int]:
        return await self.dao.poll.get_polled_teams()

    async def get_by_ids_with_user_and_pit(self, ids: Iterable[int]) -> list[dto.VotedPlayer]:
        return await self.dao.player.get_by_ids_with_user_and_pit(ids)

    async def get_dict_player_vote(self, team_id: int) -> dict[int, Played]:
        return await self.dao.poll.get_dict_player_vote(team_id)

    async def get_by_id(self, id_: int) -> dto.Team:
        return await self.dao.team.get_by_id(id_)

    async def get_by_player_or_none(
        self, game: dto.Game, player: dto.Player
    ) -> dto.SecondaryOrganizer | None:
        return await self.dao.organizer.get_by_player_or_none(game=game, player=player)

    async def get_by_player(self, game: dto.Game, player: dto.Player) -> dto.SecondaryOrganizer:
        return await self.dao.organizer.get_by_player(game=game, player=player)


@dataclass
class AdminPollReaderImpl(AdminPollReader):
    dao: HolderDao

    async def get_polled_teams(self) -> list[int]:
        return await self.dao.poll.get_polled_teams()

    async def get_by_ids_with_user_and_pit(self, ids: Iterable[int]) -> list[dto.VotedPlayer]:
        return await self.dao.player.get_by_ids_with_user_and_pit(ids)

    async def get_dict_player_vote(self, team_id: int) -> dict[int, Played]:
        return await self.dao.poll.get_dict_player_vote(team_id)

    async def get_by_id(self, id_: int) -> dto.Team:
        return await self.dao.team.get_by_id(id_)


@dataclass
class PollVoteRemoverImpl(PollVoteRemover):
    dao: HolderDao

    async def del_player_vote(self, team_id: int, player_id: int) -> None:
        return await self.dao.poll.del_player_vote(team_id, player_id)


@dataclass
class AdminGameWaiversReaderImpl(AdminGameWaiversReader):
    dao: HolderDao

    async def get_by_id(self, id_: int) -> dto.Game:
        try:
            return await self.dao.game.get_by_id(id_)
        except NoResultFound as e:
            raise exceptions.GameNotFound(game_id=id_) from e

    async def get_played_teams(self, game: dto.Game) -> Iterable[dto.Team]:
        return await self.dao.waiver.get_played_teams(game)

    async def get_played(self, game: dto.Game, team: dto.Team) -> Iterable[dto.VotedPlayer]:
        return await self.dao.waiver.get_played(game, team)

    async def get_all_by_game(self, game: dto.Game) -> list[dto.Waiver]:
        return await self.dao.waiver.get_all_by_game(game)
