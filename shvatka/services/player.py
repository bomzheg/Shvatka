import logging

from shvatka.dal.player import (
    PlayerUpserter, PlayerTeamChecker, PlayerPromoter, TeamJoiner, TeamLeaver, PlayerInTeamGetter,
)
from shvatka.models import dto
from shvatka.utils.defaults_constants import DEFAULT_ROLE, EMOJI_BY_ROLE, DEFAULT_EMOJI
from shvatka.utils.exceptions import PlayerRestoredInTeam, CantBeAuthor, PromoteError, PlayerNotInTeam, PermissionsError

logger = logging.getLogger(__name__)


async def upsert_player(user: dto.User, dao: PlayerUpserter) -> dto.Player:
    player_user = await dao.upsert_player(user)
    await dao.commit()
    return player_user


async def have_team(player: dto.Player, dao: PlayerTeamChecker) -> bool:
    return await dao.have_team(player)


async def get_my_team(player: dto.Player, dao: PlayerTeamChecker) -> dto.Team:
    return await dao.get_team(player)


async def get_my_role(player: dto.Player, dao: PlayerTeamChecker) -> str:
    return (await dao.get_player_in_team(player)).role


async def get_my_emoji(player: dto.Player, dao: PlayerTeamChecker) -> str:
    pit = await dao.get_player_in_team(player)
    return pit.emoji or EMOJI_BY_ROLE.get(pit.role, DEFAULT_EMOJI)


async def promote(actor: dto.Player, target: dto.Player, dao: PlayerPromoter):
    if not actor.can_be_author:
        raise CantBeAuthor(
            notify_user="Чтобы повысить другого пользователя - "
                        "нужно самому обладать такими правами",
            player=actor,
        )
    if target.can_be_author:
        raise PromoteError(
            text="user already have author rights",
            player=actor,
        )
    await dao.promote(actor, target)
    await dao.commit()
    logger.info("player %s promoted for target %s", actor.id, target.id)


async def join_team(
    player: dto.Player, team: dto.Team, manager: dto.Player,
    dao: TeamJoiner, role: str = DEFAULT_ROLE,
):
    await dao.check_player_free(player)
    check_can_add_players(await get_team_player(manager, team, dao))
    try:
        await dao.join_team(player, team, role=role)
    except PlayerRestoredInTeam:
        await dao.commit()
        raise
    await dao.commit()


async def check_player_on_team(player: dto.Player, team: dto.Team, dao: PlayerInTeamGetter):
    pit = await dao.get_player_in_team(player)
    if pit.team_id != team.id:
        raise PlayerNotInTeam(player=player, team=team)


async def leave(player: dto.Player, remover: dto.Player, dao: TeamLeaver):
    team = await dao.get_team(player)
    if not team:
        raise PlayerNotInTeam(player=player)
    if player.id != remover.id:  # player itself always can leave
        team_player = await get_team_player(remover, team, dao)  # team of remover must be the same as player
        check_can_remove_player(team_player)  # and remover must have permission for remove
    if game := await dao.get_active_game():
        await dao.delete(dto.Waiver(
            player=player,
            game=game,
            team=team,
        ))
        await dao.del_player_vote(team_id=team.id, player_id=player.id)
    await dao.leave_team(player)
    await dao.commit()


def check_allow_be_author(player: dto.Player):
    if not player.can_be_author:
        raise CantBeAuthor(player=player)


def check_can_remove_player(team_player: dto.FullTeamPlayer):
    if not team_player.can_remove_players:
        raise PermissionsError(permission_name="can_remove_players", team=team_player.team, player=team_player.player)


def check_can_add_players(team_player: dto.FullTeamPlayer):
    if not team_player.can_add_player:
        raise PermissionsError(permission_name="can_add_player", team=team_player.team, player=team_player.player)


async def get_team_player(approver: dto.Player, team: dto.Team, dao: PlayerInTeamGetter) -> dto.FullTeamPlayer:
    team_player = dto.FullTeamPlayer.from_simple(
        team_player=await dao.get_player_in_team(approver),
        team=team, player=approver,
    )
    if team_player.team_id != team.id:
        raise PlayerNotInTeam(player=approver, team=team)
    return team_player
