from app.dao import TeamDao
from app.dao.holder import HolderDao
from app.models import dto
from app.utils.defaults_constants import CAPTAIN_ROLE


async def create_team(chat: dto.Chat, captain: dto.Player, dao: HolderDao) -> dto.Team:
    await dao.player_in_team.check_player_free(captain)
    await dao.team.check_no_team_in_chat(chat)

    team = await dao.team.create(chat, captain)
    await dao.player_in_team.join_to_team(captain, team, CAPTAIN_ROLE)
    await dao.commit()
    return team


async def get_by_chat(chat: dto.Chat, dao: TeamDao) -> dto.Team | None:
    return await dao.get_by_chat(chat)
