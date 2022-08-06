import logging

from app.dao import PlayerDao, PlayerInTeamDao
from app.models import dto
from app.utils.defaults_constants import DEFAULT_ROLE
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
    return await dao.get_role(player)


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


async def add_player_in_team(
    player: dto.Player, team: dto.Team,
    dao: PlayerInTeamDao, role: str = DEFAULT_ROLE,
):
    try:
        await dao.add_in_team(player, team, role=role)
    except PlayerRestoredInTeam:
        await dao.commit()
        raise
    await dao.commit()


def check_allow_be_author(player: dto.Player):
    if not player.can_be_author:
        raise CantBeAuthor(player=player)
