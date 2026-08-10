from shvatka.core.interfaces.dal.organizer import OrgByPlayerGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto


class PlayerIdentityProvider(IdentityProvider):
    """Identity of work running outside any request, on behalf of a known player.

    A background task knows whose authority it acts with (the player who asked
    for it), but has no telegram update or http request to derive it from. It
    is deliberately narrow: there is no chat and no team, so team-bound checks
    fail as they would for a player acting from nowhere.
    """

    def __init__(self, player: dto.Player, dao: OrgByPlayerGetter) -> None:
        self.player = player
        self.dao = dao
        self.orgs: dict[int, dto.Organizer | None] = {}

    async def get_user(self) -> dto.User | None:
        return self.player._user  # noqa: SLF001

    async def get_player(self) -> dto.Player | None:
        return self.player

    async def get_chat(self) -> dto.Chat | None:
        return None

    async def get_team(self) -> dto.Team | None:
        return None

    async def get_full_team_player(self) -> dto.FullTeamPlayer | None:
        return None

    async def get_org(self, game: dto.Game) -> dto.Organizer | None:
        if game.id in self.orgs:
            return self.orgs[game.id]
        if game.author.id == self.player.id:
            org: dto.Organizer | None = dto.PrimaryOrganizer(player=game.author, game=game)
        else:
            org = await self.dao.get_by_player_or_none(game=game, player=self.player)
        self.orgs[game.id] = org
        return org
