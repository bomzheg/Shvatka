from typing import Sequence

from shvatka.core.interfaces.dal.complex import TeamMerger
from shvatka.core.interfaces.dal.team import (
    TeamCreator,
    TeamGetter,
    TeamRenamer,
    TeamDescChanger,
    TeamsGetter,
    TeamByIdGetter,
    PlayedGamesByTeamGetter,
    FreeForumTeamGetter,
    ByForumTeamIdGetter,
)
from shvatka.core.models import dto
from shvatka.core.models import enums
from shvatka.core.services.player import check_allow_be_author
from shvatka.core.utils.defaults_constants import CAPTAIN_ROLE
from shvatka.core.utils.exceptions import SHDataBreach, PermissionsError
from shvatka.core.views.game import GameLogWriter, GameLogEvent, GameLogType


async def create_team(
    chat: dto.Chat,
    captain: dto.Player,
    dao: TeamCreator,
    game_log: GameLogWriter,
) -> dto.Team:
    check_allow_be_author(captain)
    await dao.check_player_free(captain)
    await dao.check_no_team_in_chat(chat)

    team = await dao.create(chat, captain)
    await dao.join_team(captain, team, CAPTAIN_ROLE, as_captain=True)
    await dao.commit()
    await game_log.log(
        GameLogEvent(
            GameLogType.TEAM_CREATED,
            data=dict(
                team=team.name,
                captain=captain.name_mention,
            ),
        )
    )
    return team


async def get_by_chat(chat: dto.Chat, dao: TeamGetter) -> dto.Team | None:
    return await dao.get_by_chat(chat)


async def rename_team(
    team: dto.Team, captain: dto.FullTeamPlayer, new_name: str, dao: TeamRenamer
):
    check_can_change_name(team=team, captain=captain)
    await dao.rename_team(team=team, new_name=new_name)
    await dao.commit()


async def change_team_desc(
    team: dto.Team, captain: dto.FullTeamPlayer, new_desc: str, dao: TeamDescChanger
):
    check_can_change_name(team=team, captain=captain)
    await dao.change_team_desc(team=team, new_desc=new_desc)
    await dao.commit()


async def get_teams(dao: TeamsGetter) -> list[dto.Team]:
    return await dao.get_teams()


async def get_team_by_id(team_id: int, dao: TeamByIdGetter) -> dto.Team:
    return await dao.get_by_id(team_id)


async def get_played_games(team: dto.Team, dao: PlayedGamesByTeamGetter) -> list[dto.Game]:
    return await dao.get_played_games(team)


async def get_free_forum_teams(dao: FreeForumTeamGetter) -> Sequence[dto.ForumTeam]:
    return await dao.get_free_forum_teams()


async def get_team_by_forum_team_id(forum_team_id: int, dao: ByForumTeamIdGetter) -> dto.Team:
    return await dao.get_by_forum_team_id(forum_team_id)


async def merge_teams(
    manager: dto.Player,
    primary: dto.Team,
    secondary: dto.Team,
    game_log: GameLogWriter,
    dao: TeamMerger,
):
    if secondary.has_chat():
        raise SHDataBreach(
            team=secondary,
            notify_user="невозможно привязать такую команду к этой "
                        "(та уже имеет активный чат)",
        )
    if primary.has_forum_team():
        raise SHDataBreach(
            team=primary,
            notify_user="невозможно привязать к этой команде ещё одну "
            "(эта уже имеет привязанную команду на форуме)",
        )
    await dao.replace_team_waiver(primary, secondary)
    await dao.replace_team_keys(primary, secondary)
    await dao.replace_team_levels(primary, secondary)
    await dao.replace_team_players(primary, secondary)
    await dao.replace_forum_team(primary, secondary)
    await dao.delete(secondary)
    await dao.commit()
    await game_log.log(
        GameLogEvent(
            GameLogType.TEAMS_MERGED,
            dict(
                captain=manager.name_mention,
                primary_team=primary.name,
                secondary_team=secondary.name,
            ),
        )
    )


def check_can_change_name(team: dto.Team, captain: dto.FullTeamPlayer):
    if team.id != captain.team_id or captain.team_id != captain.team.id:
        raise SHDataBreach(
            team=team, player=captain.player, notify_user="Вы не игрок этой команды"
        )
    assert captain.player is not None
    assert team.captain is not None
    if team.captain.id == captain.player.id:
        return
    if captain.can_change_team_name:
        return
    raise PermissionsError(
        permission_name=enums.TeamPlayerPermission.can_change_team_name.name,
        team=team,
        player=captain.player,
    )
