from dataclasses import dataclass

from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto


@dataclass(kw_only=True)
class MockIdentityProvider(IdentityProvider):
    user: dto.User | None = None
    player: dto.Player | None = None
    team: dto.Team | None = None
    chat: dto.Chat | None = None
    full_team_player: dto.FullTeamPlayer | None = None

    async def get_chat(self) -> dto.Chat | None:
        return self.chat

    async def get_player(self) -> dto.Player | None:
        return self.player

    async def get_team(self) -> dto.Team | None:
        return self.team

    async def get_user(self) -> dto.User | None:
        return self.user

    async def get_full_team_player(self) -> dto.FullTeamPlayer | None:
        return self.full_team_player
