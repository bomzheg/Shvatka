from typing import Protocol


from shvatka.core.models import dto
from shvatka.core.utils import exceptions


class IdentityProvider(Protocol):
    async def get_user(self) -> dto.User | None:
        raise NotImplementedError

    async def get_player(self) -> dto.Player | None:
        raise NotImplementedError

    async def get_chat(self) -> dto.Chat | None:
        raise NotImplementedError

    async def get_team(self) -> dto.Team | None:
        raise NotImplementedError

    async def get_full_team_player(self) -> dto.FullTeamPlayer | None:
        raise NotImplementedError

    async def get_org(self, game: dto.Game) -> dto.Organizer | None:
        raise NotImplementedError

    async def get_superuser(self) -> dto.Player:
        """Resolve the acting player and ensure they may use the admin panel.

        By default nobody is a superuser; edges that expose the admin panel
        override this to check the player against the configured superusers, log
        the attempt, and return the player. Non-superusers always raise
        :class:`exceptions.NotAuthorizedForAdmin`.
        """
        raise exceptions.NotAuthorizedForAdmin(player=await self.get_player())

    async def get_required_user(self) -> dto.User:
        user = await self.get_user()
        if user is None:
            raise exceptions.UserNotFoundError
        return user

    async def get_required_user_db_id(self) -> int:
        user = await self.get_required_user()
        if user.db_id is None:
            raise exceptions.UserNotFoundError
        return user.db_id

    async def get_required_player(self) -> dto.Player:
        player = await self.get_player()
        if player is None:
            raise exceptions.PlayerNotFoundError
        return player

    async def get_required_team(self) -> dto.Team:
        team = await self.get_team()
        if team is None:
            raise exceptions.PlayerNotInTeam(
                player=await self.get_player(),
                user=await self.get_user(),
            )
        return team

    async def get_required_full_team_player(self) -> dto.FullTeamPlayer:
        full_team_player = await self.get_full_team_player()
        if full_team_player is None:
            player = await self.get_player()
            raise exceptions.PlayerNotInTeam(player=player)
        return full_team_player

    async def get_required_org(self, game: dto.Game) -> dto.Organizer:
        org = await self.get_org(game)
        if org is None:
            user = await self.get_user()
            player = await self.get_player()
            raise exceptions.IsNotOrganizer(user=user, player=player, game_id=game.id)
        return org
