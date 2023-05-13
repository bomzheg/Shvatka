import logging
from typing import Sequence

from shvatka.core.interfaces.dal.player import (
    PlayerUpserter,
    PlayerTeamChecker,
    PlayerPromoter,
    TeamJoiner,
    TeamLeaver,
    TeamPlayersGetter,
    TeamPlayerGetter,
    PlayerByIdGetter,
    TeamPlayerPermissionFlipper,
    TeamPlayerRoleUpdater,
    TeamPlayerEmojiUpdater,
    PlayerMerger,
    TeamPlayerFullHistoryGetter,
)
from shvatka.core.interfaces.dal.secure_invite import InviteSaver, InviteRemover, InviterDao
from shvatka.core.models import dto
from shvatka.core.models import enums
from shvatka.core.models.enums.invite_type import InviteType
from shvatka.core.utils import exceptions
from shvatka.core.utils.defaults_constants import DEFAULT_ROLE, EMOJI_BY_ROLE, DEFAULT_EMOJI
from shvatka.core.utils.exceptions import (
    PlayerRestoredInTeam,
    CantBeAuthor,
    PromoteError,
    PlayerNotInTeam,
    PermissionsError,
    SaltError,
)
from shvatka.core.views.game import GameLogWriter, GameLogEvent, GameLogType

logger = logging.getLogger(__name__)


async def upsert_player(user: dto.User, dao: PlayerUpserter) -> dto.Player:
    player_user = await dao.upsert_player(user)
    await dao.commit()
    return player_user


async def have_team(player: dto.Player, dao: PlayerTeamChecker) -> bool:
    return await dao.have_team(player)


async def get_my_team(player: dto.Player, dao: PlayerTeamChecker) -> dto.Team | None:
    return await dao.get_team(player)


async def get_player_by_id(id_: int, dao: PlayerByIdGetter) -> dto.Player:
    return await dao.get_by_id(id_)


async def get_player_with_stat(id_: int, dao) -> dto.PlayerWithStat:
    return await dao.get_player_with_stat(id_)


async def get_team_player_by_player(player: dto.Player, dao: PlayerTeamChecker) -> dto.TeamPlayer:
    return await dao.get_team_player(player)


async def get_my_role(player: dto.Player, dao: PlayerTeamChecker) -> str:
    return (await get_team_player_by_player(player, dao)).role


async def get_my_emoji(player: dto.Player, dao: PlayerTeamChecker) -> str:
    team_player = await get_team_player_by_player(player, dao)
    return team_player.emoji or EMOJI_BY_ROLE.get(team_player.role, DEFAULT_EMOJI)


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
    player: dto.Player,
    team: dto.Team,
    manager: dto.Player,
    dao: TeamJoiner,
    role: str = DEFAULT_ROLE,
):
    await dao.check_player_free(player)
    check_can_add_players(await get_full_team_player(manager, team, dao))
    try:
        await dao.join_team(player, team, role=role)
    except PlayerRestoredInTeam:
        await dao.commit()
        raise
    await dao.commit()


async def get_checked_player_on_team(
    player: dto.Player, team: dto.Team, dao: TeamPlayerGetter
) -> dto.TeamPlayer:
    tp = await dao.get_team_player(player)
    check_team_player_on_team(tp, team)
    return tp


def check_team_player_on_team(team_player: dto.TeamPlayer, team: dto.Team):
    if team is None or team_player.team_id != team.id:
        raise PlayerNotInTeam(player_id=team_player.player_id, team=team)


async def change_role(
    player: dto.Player, team: dto.Team, manager: dto.Player, role: str, dao: TeamPlayerRoleUpdater
) -> None:
    manager_tp = await get_full_team_player(manager, team, dao)
    check_can_manage_players(manager_tp)
    tp = await get_checked_player_on_team(player, team, dao)
    await dao.change_role(tp, role)
    await dao.commit()


async def change_emoji(
    player: dto.Player,
    team: dto.Team,
    manager: dto.Player,
    emoji: str,
    dao: TeamPlayerEmojiUpdater,
) -> None:
    manager_tp = await get_full_team_player(manager, team, dao)
    check_can_manage_players(manager_tp)
    tp = await get_checked_player_on_team(player, team, dao)
    await dao.change_emoji(tp, emoji)
    await dao.commit()


async def leave(player: dto.Player, remover: dto.Player, dao: TeamLeaver):
    team = await dao.get_team(player)
    if not team:
        raise PlayerNotInTeam(player=player)
    if player.id != remover.id:  # player itself always can leave
        team_player = await get_full_team_player(
            remover, team, dao
        )  # team of remover must be the same as player
        check_can_remove_player(team_player)  # and remover must have permission for remove
    if game := await dao.get_active_game():
        await dao.delete(
            dto.WaiverQuery(
                player=player,
                game=game,
                team=team,
            )
        )
        await dao.del_player_vote(team_id=team.id, player_id=player.id)
    await dao.leave_team(player)
    await dao.commit()


def check_allow_be_author(player: dto.Player):
    if not player.can_be_author:
        raise CantBeAuthor(player=player)


def check_can_manage_players(team_player: dto.FullTeamPlayer):
    if not team_player.can_manage_players:
        raise PermissionsError(
            permission_name=enums.TeamPlayerPermission.can_manage_players.name,
            team=team_player.team,
            player=team_player.player,
        )


def check_can_remove_player(team_player: dto.FullTeamPlayer):
    if not team_player.can_remove_players:
        raise PermissionsError(
            permission_name=enums.TeamPlayerPermission.can_remove_players.name,
            team=team_player.team,
            player=team_player.player,
        )


def check_can_add_players(team_player: dto.FullTeamPlayer):
    if not team_player.can_add_players:
        raise PermissionsError(
            permission_name=enums.TeamPlayerPermission.can_add_players.name,
            team=team_player.team,
            player=team_player.player,
        )


async def get_full_team_player(
    player: dto.Player, team: dto.Team, dao: TeamPlayerGetter
) -> dto.FullTeamPlayer:
    team_player = dto.FullTeamPlayer.from_simple(
        team_player=await get_checked_player_on_team(player, team, dao),
        team=team,
        player=player,
    )
    return team_player


async def get_team_players(team: dto.Team, dao: TeamPlayersGetter) -> Sequence[dto.FullTeamPlayer]:
    players = await dao.get_players(team)
    if team.has_forum_team() and team.has_chat():
        players = [p for p in players if p.player.has_user()]
    return players


async def save_promotion_invite(inviter: dto.Player, dao: InviteSaver) -> str:
    return await dao.save_new_invite(
        dct=dict(inviter_id=inviter.id, type_=InviteType.promote_author.name)
    )


async def check_promotion_invite(inviter: dto.Player, token: str, dao: InviterDao):
    data = await dao.get_invite(token)
    if data["type_"] != InviteType.promote_author.name:
        raise SaltError(
            text="Ошибка нарушения данных. Токен в зашифрованной и открытой части не совпал",
            alarm=True,
        )
    if data["inviter_id"] != inviter.id:
        raise SaltError(
            text="Ошибка нарушения данных. Токен в зашифрованной и открытой части не совпал",
            alarm=True,
        )


async def save_promotion_confirm_invite(inviter: dto.Player, dao: InviteSaver) -> str:
    return await dao.save_new_invite(
        dct=dict(inviter_id=inviter.id, type_=InviteType.promotion_confirm.name),
        token_len=16,
    )


async def dismiss_promotion(token: str, dao: InviteRemover):
    await dao.remove_invite(token)


async def merge_players(
    primary: dto.Player,
    secondary: dto.Player,
    game_log: GameLogWriter,
    dao: PlayerMerger,
):
    if primary.has_forum_user():
        raise exceptions.SHDataBreach(
            player=primary,
            notify_user="Невозможно привязать к тебе ещё один форумный аккаунт "
            "(ведь у тебя уже есть форумный аккаунт)",
        )
    if secondary.has_user():
        raise exceptions.SHDataBreach(
            player=secondary,
            notify_user="Невозможно привязать к тебе этот форумный аккаунт "
            "(этот аккаунт уже привязан к другому пользователю)",
        )
    await dao.replace_player_keys(primary, secondary)
    await dao.replace_player_org(primary, secondary)
    await dao.replace_games_author(primary, secondary)
    await dao.replace_levels_author(primary, secondary)
    await dao.replace_file_info(primary, secondary)
    await merge_team_history(primary, secondary, dao)
    await dao.replace_player_waiver(primary, secondary)
    await dao.replace_forum_player(primary, secondary)
    await dao.delete_player(secondary)

    await dao.commit()
    await game_log.log(
        GameLogEvent(
            GameLogType.PLAYERS_MERGED,
            dict(
                primary=primary.name_mention,
                secondary=secondary.name_mention,
            ),
        )
    )


async def merge_team_history(primary: dto.Player, secondary: dto.Player, dao: PlayerMerger):
    primary_history = await dao.get_player_teams_history(primary)
    secondary_history = await dao.get_player_teams_history(secondary)
    merged = []
    if len(primary_history) == 1 and secondary_history[-1].team_id == primary_history[0].team_id:
        if primary_history[0].date_joined > secondary_history[0].date_joined:
            merged = secondary_history
    if not merged:
        merged = list(sorted(primary_history + secondary_history, key=lambda tp: tp.date_joined))
    for tp1, tp2 in zip(merged[:-1:], merged[1::]):
        if tp1.date_left is None or (tp1.date_left > tp2.date_joined):
            raise ValueError("can't join automatically")
    for tp in merged:
        tp.player_id = primary.id
    await dao.clean_history(primary)
    await dao.clean_history(secondary)
    await dao.set_history(merged)


async def agree_promotion(
    token: str,
    inviter_id: int,
    target: dto.Player,
    dao: PlayerPromoter,
):
    data = await dao.get_invite(token)
    if data["type_"] != InviteType.promotion_confirm.name:
        raise SaltError(
            text="Ошибка нарушения данных. Токен в зашифрованной и открытой части не совпал",
            alarm=True,
        )
    if data["inviter_id"] != inviter_id:
        raise SaltError(
            text="Ошибка нарушения данных. Токен в зашифрованной и открытой части не совпал",
            alarm=True,
        )
    inviter = await dao.get_by_id(inviter_id)
    await promote(inviter, target, dao)


async def get_teams_history(
    player: dto.Player, dao: TeamPlayerFullHistoryGetter
) -> list[dto.FullTeamPlayer]:
    return await dao.get_full_history(player)


async def flip_permission(
    actor: dto.FullTeamPlayer,
    team_player: dto.TeamPlayer,
    permission: enums.TeamPlayerPermission,
    dao: TeamPlayerPermissionFlipper,
):
    check_can_manage_players(actor)
    if actor.player_id == team_player.player_id:
        raise exceptions.PermissionsError(
            permission_name=enums.TeamPlayerPermission.can_manage_players.name,
            notify_user="can't edit yourself",
            player=actor.player,
            team=actor.team,
        )
    await dao.flip_permission(team_player, permission)
    await dao.commit()
