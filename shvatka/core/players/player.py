import logging
from typing import Sequence

from shvatka.core.players.dto import TimelineItem, WaiverPoint
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
    TeamPlayerFullHistoryGetter,
    PlayerByUserIdGetter,
    PlayerWaiversGetter,
)
from shvatka.core.interfaces.dal.secure_invite import InviteSaver, InviteRemover, InviterDao
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models import enums
from shvatka.core.models.enums.invite_type import InviteType
from shvatka.core.players.interfaces import PlayerUsernameChanger, UserPasswordSetter, PlayerMerger
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
from shvatka.core.views.team import TeamNotifier, PlayerJoinedTeam, PlayerLeftTeam

logger = logging.getLogger(__name__)


async def upsert_player(user: dto.User, dao: PlayerUpserter) -> dto.Player:
    player_user = await dao.upsert_player(user)
    await dao.commit()
    return player_user


async def set_player_username(player: dto.Player, username: str, dao: PlayerUsernameChanger):
    if not is_same_username(player, username) and await dao.is_username_occupied(username):
        raise exceptions.PlayerUsernameOccupied
    await dao.set_username(player, username)
    await dao.commit()


def is_same_username(player: dto.Player, username: str) -> bool:
    if not player.username:
        return False
    return player.username.strip().lower() == username.strip().lower()


async def have_team(player: dto.Player, dao: PlayerTeamChecker) -> bool:
    return await dao.have_team(player)


async def get_my_team(player: dto.Player, dao: PlayerTeamChecker) -> dto.Team | None:
    return await dao.get_team(player)


async def get_player_by_id(id_: int, dao: PlayerByIdGetter) -> dto.Player:
    return await dao.get_by_id(id_)


async def get_player_by_user_id(user_id: int, dao: PlayerByUserIdGetter) -> dto.Player:
    return await dao.get_by_user_id(user_id)


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
    notifier: TeamNotifier,
    role: str = DEFAULT_ROLE,
    emoji: str | None = None,
):
    await dao.check_player_free(player)
    await check_can_add_players(manager, team, dao)
    try:
        await dao.join_team(player, team, role=role, emoji=emoji)
    except PlayerRestoredInTeam:
        # the player was previously in this team and is restored rather than re-created;
        # we still commit and notify, then re-raise so callers can react to the restore
        await dao.commit()
        await notifier.notify(PlayerJoinedTeam(team=team, actor=manager, invited=player))
        raise
    await dao.commit()
    logger.info(
        "Captain %s added to team %s player %s",
        manager.id,
        team.id,
        player.id,
    )
    await notifier.notify(PlayerJoinedTeam(team=team, actor=manager, invited=player))


def is_team_captain(team: dto.Team, player: dto.Player) -> bool:
    return team.captain is not None and team.captain.id == player.id


async def get_checked_player_on_team(
    player: dto.Player, team: dto.Team | None, dao: TeamPlayerGetter
) -> dto.TeamPlayer:
    tp = await dao.get_team_player(player)
    check_team_player_on_team(tp, team)
    return tp


def check_team_player_on_team(team_player: dto.TeamPlayer, team: dto.Team | None) -> None:
    if team is None or team_player.team_id != team.id:
        raise PlayerNotInTeam(player_id=team_player.player_id, team=team)


async def change_role(
    player: dto.Player, team: dto.Team, manager: dto.Player, role: str, dao: TeamPlayerRoleUpdater
) -> None:
    await check_can_manage_players(manager, team, dao)
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
    await check_can_manage_players(manager, team, dao)
    tp = await get_checked_player_on_team(player, team, dao)
    await dao.change_emoji(tp, emoji)
    await dao.commit()


async def leave(
    player: dto.Player,
    remover: dto.Player,
    dao: TeamLeaver,
    notifier: TeamNotifier,
):
    team = await dao.get_team(player)
    if not team:
        raise PlayerNotInTeam(player=player)
    if player.id != remover.id:  # player itself always can leave
        await check_can_remove_player(remover, team, dao)
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
    await notifier.notify(PlayerLeftTeam(team=team, actor=remover, removed=player))


def check_allow_be_author(player: dto.Player):
    if not player.can_be_author:
        raise CantBeAuthor(player=player)


async def check_can_manage_players(
    actor: dto.Player, team: dto.Team, dao: TeamPlayerGetter
) -> None:
    # the captain is allowed to manage the team even if they temporarily left it
    if is_team_captain(team, actor):
        return
    assert_can_manage_players(await get_full_team_player(actor, team, dao))


def assert_can_manage_players(team_player: dto.FullTeamPlayer) -> None:
    if not team_player.can_manage_players:
        raise PermissionsError(
            permission_name=enums.TeamPlayerPermission.can_manage_players.name,
            team=team_player.team,
            player=team_player.player,
        )


async def check_can_remove_player(
    actor: dto.Player, team: dto.Team, dao: TeamPlayerGetter
) -> None:
    if is_team_captain(team, actor):
        return
    team_player = await get_full_team_player(actor, team, dao)
    if not team_player.can_remove_players:
        raise PermissionsError(
            permission_name=enums.TeamPlayerPermission.can_remove_players.name,
            team=team_player.team,
            player=team_player.player,
        )


async def check_can_add_players(actor: dto.Player, team: dto.Team, dao: TeamPlayerGetter) -> None:
    if is_team_captain(team, actor):
        return
    team_player = await get_full_team_player(actor, team, dao)
    if not team_player.can_add_players:
        raise PermissionsError(
            permission_name=enums.TeamPlayerPermission.can_add_players.name,
            team=team_player.team,
            player=team_player.player,
        )


async def get_full_team_player(
    player: dto.Player, team: dto.Team | None, dao: TeamPlayerGetter
) -> dto.FullTeamPlayer:
    team_player = await get_full_team_player_or_none(player=player, team=team, dao=dao)
    if team_player is None:
        raise exceptions.PlayerNotInTeam(player_id=player.id)
    return team_player


async def get_full_team_player_or_none(
    player: dto.Player, team: dto.Team | None, dao: TeamPlayerGetter
) -> dto.FullTeamPlayer | None:
    if team is None:
        return None
    try:
        team_player = dto.FullTeamPlayer.from_simple(
            team_player=await get_checked_player_on_team(player, team, dao),
            team=team,
            player=player,
        )
    except exceptions.PlayerNotInTeam:
        return None
    return team_player


async def get_team_players(team: dto.Team, dao: TeamPlayersGetter) -> Sequence[dto.FullTeamPlayer]:
    players = await dao.get_players(team)
    if team.has_forum_team() and team.has_chat():
        players = [p for p in players if p.player.has_user()]
    return players


async def save_promotion_invite(inviter: dto.Player, dao: InviteSaver) -> str:
    return await dao.save_new_invite(
        dct={"inviter_id": inviter.id, "type_": InviteType.promote_author.name}
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
        dct={"inviter_id": inviter.id, "type_": InviteType.promotion_confirm.name},
        token_len=16,
    )


async def dismiss_promotion(token: str, dao: InviteRemover):
    await dao.remove_invite(token)


async def merge_players(
    primary: dto.Player,
    secondary: dto.Player,
    game_log: GameLogWriter,
    dao: PlayerMerger,
    timeline: list[TimelineItem] | None = None,
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
    if timeline is not None:
        timeline = normalize_timeline(timeline)
        points = await get_waiver_points(primary, dao) + await get_waiver_points(secondary, dao)
        check_timeline_matches_points(timeline, points)
    primary_email = await dao.get_email_by_player_id(primary.id)
    secondary_email = await dao.get_email_by_player_id(secondary.id)
    if primary_email is not None:
        if secondary_email is not None:
            await dao.delete_email(secondary_email)
    elif secondary_email is not None:
        await dao.replace_email_player(secondary_email, primary.id)

    await dao.replace_player_keys(primary, secondary)
    await dao.replace_player_org(primary, secondary)
    await dao.replace_games_author(primary, secondary)
    await dao.replace_levels_author(primary, secondary)
    await dao.replace_file_info(primary, secondary)
    if timeline is not None:
        await set_merged_team_history(primary, secondary, timeline, dao)
    else:
        await merge_team_history(primary, secondary, dao)
    await dao.replace_player_waiver(primary, secondary)
    await dao.replace_forum_player(primary, secondary)
    await dao.delete_player(secondary)

    await dao.commit()
    await game_log.log(
        GameLogEvent(
            GameLogType.PLAYERS_MERGED,
            {
                "primary": primary.name_mention,
                "secondary": secondary.name_mention,
            },
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
        merged = sorted(primary_history + secondary_history, key=lambda tp: tp.date_joined)
    for tp1, tp2 in zip(merged[:-1:], merged[1::]):
        if tp1.date_left is None or (tp1.date_left > tp2.date_joined):
            raise exceptions.MergeError(
                player=primary,
                text="team histories are not compatible, can't merge automatically",
                notify_user="Истории команд игроков несовместимы, автоматическое объединение "
                "невозможно — требуется вручную задать таймлайн (timeline)",
            )
    for tp in merged:
        tp.player_id = primary.id
    await dao.clean_history(primary)
    await dao.clean_history(secondary)
    await dao.set_history(merged)


async def get_waiver_points(player: dto.Player, dao: PlayerWaiversGetter) -> list[WaiverPoint]:
    """Return intervals in which the player's team membership is fixed by waivers.

    Only waivers with vote ``yes`` for games with a known start date pin the player
    to a team: around the game start the player certainly acted as a team member.
    """
    waivers = await dao.get_player_waivers(player)
    points = [
        WaiverPoint.from_waiver(waiver)
        for waiver in waivers
        if waiver.played.can_play and waiver.game.start_at is not None
    ]
    return sorted(points, key=lambda point: point.at_since)


def normalize_timeline(timeline: list[TimelineItem]) -> list[TimelineItem]:
    """Sort the timeline and check that it forms a valid membership history."""
    if not timeline:
        raise exceptions.MergeError(
            text="timeline is empty",
            notify_user="Таймлайн не может быть пустым",
        )
    timeline = sorted(timeline, key=lambda item: item.date_joined)
    for item in timeline:
        if item.date_left is not None and item.date_left <= item.date_joined:
            raise exceptions.MergeError(
                text=f"timeline item for team {item.team_id} ends before it starts",
                notify_user="Дата выхода из команды должна быть позже даты вступления",
            )
    for current, following in zip(timeline[:-1], timeline[1:]):
        if current.date_left is None or current.date_left > following.date_joined:
            raise exceptions.MergeError(
                text=f"timeline items for teams {current.team_id} "
                f"and {following.team_id} overlap",
                notify_user="Интервалы таймлайна пересекаются — игрок не может быть "
                "в двух командах одновременно",
            )
    return timeline


def check_timeline_matches_points(timeline: list[TimelineItem], points: list[WaiverPoint]) -> None:
    for point in points:
        if not any(
            item.team_id == point.team.id
            and item.date_joined <= point.at_since
            and (item.date_left is None or item.date_left >= point.at_until)
            for item in timeline
        ):
            raise exceptions.MergeError(
                team=point.team,
                text=f"timeline violates waiver point: "
                f"game {point.game.id} requires team {point.team.id} "
                f"from {point.at_since} to {point.at_until}",
                notify_user=f"Таймлайн нарушает вейвер: во время игры «{point.game.name}» "
                f"(с {point.at_since:%d.%m.%Y %H:%M} по {point.at_until:%d.%m.%Y %H:%M}) "
                f"игрок должен состоять в команде «{point.team.name}»",
            )


async def set_merged_team_history(
    primary: dto.Player,
    secondary: dto.Player,
    timeline: list[TimelineItem],
    dao: PlayerMerger,
) -> None:
    """Replace both players' team histories with the manually built timeline.

    Role, emoji and permissions are inherited from the latest existing membership
    in the same team (of either player), falling back to plain defaults.
    """
    history = await dao.get_player_teams_history(primary)
    history += await dao.get_player_teams_history(secondary)
    last_by_team: dict[int, dto.TeamPlayer] = {
        tp.team_id: tp for tp in sorted(history, key=lambda tp: tp.date_joined)
    }
    merged = []
    for item in timeline:
        source = last_by_team.get(item.team_id)
        merged.append(
            dto.TeamPlayer(
                id=source.id if source else 0,
                player_id=primary.id,
                team_id=item.team_id,
                date_joined=item.date_joined,
                date_left=item.date_left,
                role=source.role if source else DEFAULT_ROLE,
                emoji=source.emoji if source else None,
                _can_manage_waivers=source._can_manage_waivers if source else False,  # noqa: SLF001
                _can_manage_players=source._can_manage_players if source else False,  # noqa: SLF001
                _can_change_team_name=source._can_change_team_name if source else False,  # noqa: SLF001
                _can_add_players=source._can_add_players if source else False,  # noqa: SLF001
                _can_remove_players=source._can_remove_players if source else False,  # noqa: SLF001
            )
        )
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
    assert_can_manage_players(actor)
    if actor.player_id == team_player.player_id:
        raise exceptions.PermissionsError(
            permission_name=enums.TeamPlayerPermission.can_manage_players.name,
            notify_user="can't edit yourself",
            player=actor.player,
            team=actor.team,
        )
    await dao.flip_permission(team_player, permission)
    await dao.commit()


async def set_password(identity: IdentityProvider, hashed_password: str, dao: UserPasswordSetter):
    await dao.set_password(await identity.get_required_player(), hashed_password)
    await dao.commit()
