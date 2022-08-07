from app.dao.holder import HolderDao
from app.dao.redis.pool import PollDao
from app.models import dto
from app.models.dto import VotedPlayer
from app.models.enums.played import Played


async def get_voted_list(team: dto.Team, dao: HolderDao, poll: PollDao) -> dict[Played, list[VotedPlayer]]:
    poll_date = await poll.get_dict_player_vote(team.id)
    voted_players = await dao.player.get_by_ids_with_user_and_pit(poll_date.keys())
    result = {}
    for voted in voted_players:
        vote = poll_date[voted.player.id]
        result.setdefault(vote, []).append(voted)
    return result
