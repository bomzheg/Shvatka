from app.dao.holder import HolderDao
from app.models import dto
from app.models.dto import VotedPlayer
from app.models.enums.played import Played
from app.utils.exceptions import WaiverForbidden


async def get_voted_list(
    team: dto.Team, dao: HolderDao,
) -> dict[Played, list[VotedPlayer]]:
    poll_date = await dao.poll.get_dict_player_vote(team.id)
    voted_players = await dao.player.get_by_ids_with_user_and_pit(poll_date.keys())
    result = {}
    for voted in voted_players:
        vote = poll_date[voted.player.id]
        result.setdefault(vote, []).append(voted)
    return result


async def add_vote(
    game: dto.Game, team: dto.Team, player: dto.Player, vote: Played, dao: HolderDao,
):
    if await dao.waiver.is_excluded(game=game, player=player, team=team):
        raise WaiverForbidden(player=player, team=team, game=game)
    await dao.poll.add_player_vote(team.id, player.id, vote.name)
