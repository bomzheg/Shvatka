import typing
from typing import Iterable, Sequence

from shvatka.core.interfaces.dal.waiver import (
    WaiverVoteAdder,
    WaiverVoteGetter,
    WaiverApprover,
    GameWaiversGetter,
    WaiverGetter,
)
from shvatka.core.models import dto
from shvatka.core.models import enums
from shvatka.core.models.enums.played import Played
from shvatka.core.services.player import get_checked_player_on_team, get_full_team_player
from shvatka.core.utils.exceptions import WaiverForbidden, PermissionsError


async def get_vote_to_voted(
    team: dto.Team,
    dao: WaiverVoteGetter,
) -> dict[Played, list[dto.VotedPlayer]]:
    result: dict[Played, list[dto.VotedPlayer]] = {}
    for vote in await get_voted_list(team, dao):
        result.setdefault(vote.vote, []).append(dto.VotedPlayer(player=vote.player, pit=vote.pit))
    return result


async def get_all_played(
    game: dto.Game, dao: GameWaiversGetter
) -> dict[dto.Team, Iterable[dto.VotedPlayer]]:
    teams = await dao.get_played_teams(game)
    result = {}
    for team in teams:
        players = await dao.get_played(game, team)
        result[team] = players
    return result


async def get_voted_list(
    team: dto.Team,
    dao: WaiverVoteGetter,
) -> list[dto.Vote]:
    poll_date = await dao.get_dict_player_vote(team.id)
    voted_players = await dao.get_by_ids_with_user_and_pit(poll_date.keys())
    result = []
    for voted in voted_players:
        vote = poll_date[voted.player.id]
        result.append(dto.Vote(player=voted.player, pit=voted.pit, vote=vote))
    return result


async def add_vote(
    game: dto.Game,
    team: dto.Team,
    player: dto.Player,
    vote: Played,
    dao: WaiverVoteAdder,
):
    if await dao.is_excluded(game=game, player=player, team=team):
        raise WaiverForbidden(player=player, team=team, game=game)
    await force_add_vote(game=game, team=team, player=player, vote=vote, dao=dao)


async def force_add_vote(
    game: dto.Game,
    team: dto.Team,
    player: dto.Player,
    vote: Played,
    dao: WaiverVoteAdder,
):
    await get_checked_player_on_team(player, team, dao)
    await dao.add_player_vote(team.id, player.id, vote.name)


async def approve_waivers(
    game: dto.Game, team: dto.Team, approver: dto.Player, dao: WaiverApprover
):
    """
    Captain must approve waivers, for send it to orgs
    :param game:
    :param team:
    :param approver: player who approve waivers. In most case - Captain
    :param dao:
    :return:
    """
    team_player = await get_full_team_player(approver, team, dao)
    check_allow_approve_waivers(team_player)
    for vote in await get_voted_list(team, dao):
        if vote.vote == Played.not_allowed:
            continue
        waiver = dto.Waiver(
            player=vote.player,
            team=team,
            game=game,
            played=vote.vote,
        )
        await dao.upsert(waiver)
    await dao.commit()


async def get_voted_yes(team: dto.Team, dao: WaiverApprover) -> list[dto.Vote]:
    return list(filter(lambda x: x.vote == Played.yes, await get_voted_list(team, dao)))


async def get_not_played_team_players(team: dto.Team, dao: WaiverApprover) -> Sequence[dto.Player]:
    votes_yes = await get_voted_yes(team, dao)
    players = await dao.get_players(team)
    not_played = set(players) - typing.cast(set[dto.FullTeamPlayer], {v.pit for v in votes_yes})
    return tuple(sorted((tp.player for tp in not_played), key=lambda p: p.id))


async def revoke_vote_by_captain(
    game: dto.Game,
    team: dto.Team,
    approver: dto.Player,
    target: dto.Player,
    dao: WaiverApprover,
):
    team_player = await get_full_team_player(approver, team, dao)
    check_allow_approve_waivers(team_player)
    waiver = dto.Waiver(
        player=target,
        team=team,
        game=game,
        played=Played.revoked,
    )
    await dao.upsert(waiver)
    await dao.del_player_vote(team.id, target.id)
    await dao.commit()


async def get_my_waiver(
    player: dto.Player,
    team: dto.Team,
    game: dto.Game,
    dao: WaiverGetter,
) -> dto.Waiver | None:
    return await dao.get_player_waiver(player=player, team=team, game=game)


def check_allow_approve_waivers(team_player: dto.FullTeamPlayer):
    if not team_player.can_manage_waivers:
        raise PermissionsError(
            permission_name=enums.TeamPlayerPermission.can_manage_players.name,
            player=team_player.player,
            team=team_player.team,
        )
