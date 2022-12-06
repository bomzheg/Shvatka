from shvatka.dal.team import TeamCreator, TeamGetter, TeamRenamer, TeamDescChanger
from shvatka.models import dto
from shvatka.utils.defaults_constants import CAPTAIN_ROLE
from shvatka.utils.exceptions import SHDataBreach, PermissionsError


async def create_team(chat: dto.Chat, captain: dto.Player, dao: TeamCreator) -> dto.Team:
    await dao.check_player_free(captain)
    await dao.check_no_team_in_chat(chat)

    team = await dao.create(chat, captain)
    await dao.join_team(captain, team, CAPTAIN_ROLE, as_captain=True)
    await dao.commit()
    return team


async def get_by_chat(chat: dto.Chat, dao: TeamGetter) -> dto.Team | None:
    return await dao.get_by_chat(chat)


async def rename_team(team: dto.Team, captain: dto.FullTeamPlayer, new_name: str, dao: TeamRenamer):
    check_can_change_name(team=team, captain=captain)
    await dao.rename_team(team=team, new_name=new_name)
    await dao.commit()


async def change_team_desc(team: dto.Team, captain: dto.FullTeamPlayer, new_desc: str, dao: TeamDescChanger):
    check_can_change_name(team=team, captain=captain)
    await dao.change_team_desc(team=team, new_desc=new_desc)
    await dao.commit()


def check_can_change_name(team: dto.Team, captain: dto.FullTeamPlayer):
    if team.id != captain.team_id or captain.team_id != captain.team.id:
        raise SHDataBreach(team=team, player=captain.player, notify_user="Вы не игрок этой команды")
    if team.captain.id == captain.player.id:
        return
    if captain.can_change_team_name:
        return
    raise PermissionsError(permission_name="can_change_name", team=team, player=captain.player)
