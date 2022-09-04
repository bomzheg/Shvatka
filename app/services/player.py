import logging

from app.dao import PlayerDao, PlayerInTeamDao
from app.dao.holder import HolderDao
from app.models import dto
from app.utils.defaults_constants import DEFAULT_ROLE, EMOJI_BY_ROLE, DEFAULT_EMOJI
from app.utils.exceptions import PlayerRestoredInTeam, CantBeAuthor, PromoteError

logger = logging.getLogger(__name__)


async def upsert_player(user: dto.User, dao: PlayerDao) -> dto.Player:
    player_user = await dao.upsert_player(user)
    await dao.commit()
    return player_user


async def have_team(player: dto.Player, dao: PlayerInTeamDao) -> bool:
    return await dao.have_team(player)


async def get_my_team(player: dto.Player, dao: PlayerInTeamDao) -> dto.Team:
    return await dao.get_team(player)


async def get_my_role(player: dto.Player, dao: PlayerInTeamDao) -> str:
    return (await dao.get_player_in_team(player)).role


async def get_my_emoji(player: dto.Player, dao: PlayerInTeamDao) -> str:
    pit = await dao.get_player_in_team(player)
    return pit.emoji or EMOJI_BY_ROLE.get(pit.role, DEFAULT_EMOJI)


async def promote(actor: dto.Player, target: dto.Player, dao: PlayerDao):
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
    player: dto.Player, team: dto.Team,
    dao: PlayerInTeamDao, role: str = DEFAULT_ROLE,
):
    try:
        await dao.join_team(player, team, role=role)
    except PlayerRestoredInTeam:
        await dao.commit()
        raise
    await dao.commit()


async def leave(player: dto.Player, dao: HolderDao):
    if game := await dao.game.get_active_game():
        team = await dao.player_in_team.get_team(player)
        await dao.waiver.delete(dto.Waiver(
            player=player,
            game=game,
            team=team,
        ))
        await dao.poll.del_player_vote(team_id=team.id, player_id=player.id)
    await dao.player_in_team.leave_team(player)
    await dao.commit()


def check_allow_be_author(player: dto.Player):
    if not player.can_be_author:
        raise CantBeAuthor(player=player)
