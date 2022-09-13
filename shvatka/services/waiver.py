from shvatka.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.models.enums.played import Played
from shvatka.utils.exceptions import WaiverForbidden, PermissionsError


async def get_vote_to_voted(
    team: dto.Team, dao: HolderDao,
) -> dict[Played, list[dto.VotedPlayer]]:
    result = {}
    for vote in await get_voted_list(team, dao):
        result.setdefault(vote.vote, []) \
            .append(dto.VotedPlayer(player=vote.player, pit=vote.pit))
    return result


async def get_voted_list(
    team: dto.Team, dao: HolderDao,
) -> list[dto.Vote]:
    poll_date = await dao.poll.get_dict_player_vote(team.id)
    voted_players = await dao.player.get_by_ids_with_user_and_pit(poll_date.keys())
    result = []
    for voted in voted_players:
        vote = poll_date[voted.player.id]
        result.append(dto.Vote(player=voted.player, pit=voted.pit, vote=vote))
    return result


async def add_vote(
    game: dto.Game, team: dto.Team, player: dto.Player, vote: Played, dao: HolderDao,
):
    if await dao.waiver.is_excluded(game=game, player=player, team=team):
        raise WaiverForbidden(player=player, team=team, game=game)
    await dao.poll.add_player_vote(team.id, player.id, vote.name)


async def approve_waivers(game: dto.Game, team: dto.Team, approver: dto.Player, dao: HolderDao):
    await check_allow_approve_waivers(approver, team)
    for vote in await get_voted_list(team, dao):
        if vote.vote == Played.not_allowed:
            continue
        waiver = dto.Waiver(
            player=vote.player,
            team=team,
            game=game,
            played=vote.vote,
        )
        await dao.waiver.upsert(waiver)
    await dao.commit()


async def check_allow_approve_waivers(player: dto.Player, team: dto.Team):
    if team.captain.id != player.id:
        raise PermissionsError(
            permission_name="manage_waivers",
            player=player,
            team=team,
        )
