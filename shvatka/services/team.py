from shvatka.dal.team import TeamCreator, TeamGetter
from shvatka.models import dto
from shvatka.utils.defaults_constants import CAPTAIN_ROLE


async def create_team(chat: dto.Chat, captain: dto.Player, dao: TeamCreator) -> dto.Team:
    await dao.check_player_free(captain)
    await dao.check_no_team_in_chat(chat)

    team = await dao.create(chat, captain)
    await dao.join_team(captain, team, CAPTAIN_ROLE)
    await dao.commit()
    return team


async def get_by_chat(chat: dto.Chat, dao: TeamGetter) -> dto.Team | None:
    return await dao.get_by_chat(chat)
