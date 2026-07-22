"""Interactors for user-to-user action requests: team-join invites, ask-to-join
requests, org invites and merge requests, plus accept / decline / cancel and
listing.

Creating a request is the primary business operation (errors surface). Accepting
one that performs a real change reuses the existing domain services
(:func:`join_team`, org adding, :func:`merge_teams`, :func:`merge_players`) so
the change and the request resolution commit together.

Merge requests (team/player with their forum copies) target no particular
player: they are answered by any superuser, either from the web admin panel or
from the game-log channel message the bot posts. Resolving one emits
:class:`ActionRequestResolved` so every bot message for the request is removed,
and the merge itself writes the usual game-log entry.
"""

import contextlib
import logging
from collections.abc import Sequence
from dataclasses import dataclass

from shvatka.core.interfaces.dal.complex import TeamMerger
from shvatka.core.interfaces.dal.organizer import OrgAdder
from shvatka.core.interfaces.dal.player import (
    PlayerByIdGetter,
    PlayerPromoter,
    TeamJoiner,
    TeamPlayerGetter,
    TeamPlayersGetter,
)
from shvatka.core.interfaces.dal.team import TeamByIdGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.models import dto
from shvatka.core.models.enums.notification import NotificationType, NotificationSeverity
from shvatka.core.models.enums.request import RequestType, RequestStatus
from shvatka.core.notifications import dto as ndto
from shvatka.core.interfaces.bus import ActionRequestResolved, Bus
from shvatka.core.interfaces.superusers import SuperusersResolver
from shvatka.core.notifications.adapters import (
    NotificationWriter,
    RequestNotifier,
    RequestStorage,
)
from shvatka.core.players.dto import TimelineItem
from shvatka.core.players.interfaces import PlayerMerger
from shvatka.core.players.player import (
    check_allow_be_author,
    check_can_add_players,
    join_team,
    merge_players,
    promote,
)
from shvatka.core.services.game import get_game
from shvatka.core.services.organizers import check_allow_manage_orgs, get_orgs
from shvatka.core.services.team import get_team_by_id, merge_teams
from shvatka.core.utils.defaults_constants import DEFAULT_ROLE
from shvatka.core.utils.exceptions import (
    PlayerRestoredInTeam,
    PromoteError,
    RequestNotPending,
    RequestPermissionError,
)
from shvatka.core.views.game import GameLogWriter, OrgNotifier, NewOrg
from shvatka.core.views.team import TeamNotifier

logger = logging.getLogger(__name__)

MERGE_REQUEST_TYPES = (RequestType.team_merge, RequestType.player_merge)


@dataclass
class CreateTeamJoinInviteInteractor:
    """A team manager invites a player to join their team."""

    requests: RequestStorage
    notifications: NotificationWriter
    team_dao: TeamByIdGetter
    player_dao: PlayerByIdGetter
    team_player_dao: TeamPlayerGetter
    notifier: RequestNotifier

    async def __call__(
        self,
        identity: IdentityProvider,
        team_id: int,
        player_id: int,
        role: str | None = None,
        emoji: str | None = None,
    ) -> ndto.ActionRequest:
        manager = await identity.get_required_player()
        team = await get_team_by_id(team_id, self.team_dao)
        target = await self.player_dao.get_by_id(player_id)
        await check_can_add_players(manager, team, self.team_player_dao)
        existing = await self.requests.get_pending(
            type_=RequestType.team_join_invite, team_id=team_id, target_player_id=player_id
        )
        if existing is not None:
            return existing
        payload = {
            "team_id": team.id,
            "team_name": team.name,
            "role": role,
            "emoji": emoji,
            "inviter_id": manager.id,
            "inviter_name": manager.name_mention,
            "player_id": target.id,
            "player_name": target.name_mention,
        }
        request = await self.requests.create(
            type_=RequestType.team_join_invite,
            initiator_id=manager.id,
            target_player_id=target.id,
            team_id=team.id,
            payload=payload,
        )
        await self.notifications.create(
            recipient_id=target.id,
            type_=NotificationType.team_join_invite,
            severity=NotificationSeverity.normal,
            actor_id=manager.id,
            payload=payload,
            request_id=request.id,
        )
        await self.notifier.notify_created(request)
        await self.requests.commit()
        return request


@dataclass
class CreateTeamJoinRequestInteractor:
    """A player asks to join a team; team managers are notified."""

    requests: RequestStorage
    notifications: NotificationWriter
    team_dao: TeamByIdGetter
    team_players_dao: TeamPlayersGetter
    notifier: RequestNotifier

    async def __call__(self, identity: IdentityProvider, team_id: int) -> ndto.ActionRequest:
        player = await identity.get_required_player()
        team = await get_team_by_id(team_id, self.team_dao)
        existing = await self.requests.get_pending(
            type_=RequestType.team_join_request, team_id=team_id, initiator_id=player.id
        )
        if existing is not None:
            return existing
        payload = {
            "team_id": team.id,
            "team_name": team.name,
            "player_id": player.id,
            "player_name": player.name_mention,
        }
        request = await self.requests.create(
            type_=RequestType.team_join_request,
            initiator_id=player.id,
            team_id=team.id,
            payload=payload,
        )
        manager_ids = await self._manager_ids(team)
        await self.notifications.create_for_recipients(
            recipient_ids=manager_ids,
            type_=NotificationType.team_join_request,
            severity=NotificationSeverity.normal,
            actor_id=player.id,
            payload=payload,
            request_id=request.id,
        )
        await self.notifier.notify_created(request)
        await self.requests.commit()
        return request

    async def _manager_ids(self, team: dto.Team) -> set[int]:
        players = await self.team_players_dao.get_players(team)
        return {tp.player.id for tp in players if tp.is_captain or tp.can_add_players}


@dataclass
class CreateOrgInviteInteractor:
    """A game author invites a player to become an organizer."""

    requests: RequestStorage
    notifications: NotificationWriter
    player_dao: PlayerByIdGetter
    org_adder: OrgAdder
    notifier: RequestNotifier

    async def __call__(
        self, identity: IdentityProvider, game_id: int, player_id: int
    ) -> ndto.ActionRequest:
        author = await identity.get_required_player()
        game = await get_game(id_=game_id, dao=self.org_adder)
        check_allow_manage_orgs(game, author.id)
        target = await self.player_dao.get_by_id(player_id)
        existing = await self.requests.get_pending(
            type_=RequestType.org_invite, game_id=game_id, target_player_id=player_id
        )
        if existing is not None:
            return existing
        payload = {
            "game_id": game.id,
            "game_name": game.name,
            "author_id": author.id,
            "author_name": author.name_mention,
            "player_id": target.id,
            "player_name": target.name_mention,
        }
        request = await self.requests.create(
            type_=RequestType.org_invite,
            initiator_id=author.id,
            target_player_id=target.id,
            game_id=game.id,
            payload=payload,
        )
        await self.notifications.create(
            recipient_id=target.id,
            type_=NotificationType.org_invite,
            severity=NotificationSeverity.normal,
            actor_id=author.id,
            payload=payload,
            request_id=request.id,
        )
        await self.notifier.notify_created(request)
        await self.requests.commit()
        return request


@dataclass
class CreatePromotionInviteInteractor:
    """An author invites a player to be promoted to author (get "аппрув").

    The target accepts the request to actually receive author rights, mirroring
    the inline-invite / confirm flow the bot exposes.
    """

    requests: RequestStorage
    notifications: NotificationWriter
    player_dao: PlayerByIdGetter
    notifier: RequestNotifier

    async def __call__(self, identity: IdentityProvider, player_id: int) -> ndto.ActionRequest:
        author = await identity.get_required_player()
        check_allow_be_author(author)
        target = await self.player_dao.get_by_id(player_id)
        if target.can_be_author:
            raise PromoteError(text="user already have author rights", player=author)
        existing = await self.requests.get_pending(
            type_=RequestType.promotion, target_player_id=target.id
        )
        if existing is not None:
            return existing
        payload = {
            "inviter_id": author.id,
            "inviter_name": author.name_mention,
            "player_id": target.id,
            "player_name": target.name_mention,
        }
        request = await self.requests.create(
            type_=RequestType.promotion,
            initiator_id=author.id,
            target_player_id=target.id,
            payload=payload,
        )
        await self.notifications.create(
            recipient_id=target.id,
            type_=NotificationType.promotion_invite,
            severity=NotificationSeverity.normal,
            actor_id=author.id,
            payload=payload,
            request_id=request.id,
        )
        await self.notifier.notify_created(request)
        await self.requests.commit()
        return request


@dataclass
class CreateTeamMergeRequestInteractor:
    """A captain asks the admins to merge their team with its forum copy."""

    requests: RequestStorage
    notifications: NotificationWriter
    team_dao: TeamByIdGetter
    superusers: SuperusersResolver
    notifier: RequestNotifier

    async def __call__(
        self, identity: IdentityProvider, primary_team_id: int, secondary_team_id: int
    ) -> ndto.ActionRequest:
        captain = await identity.get_required_player()
        primary = await get_team_by_id(primary_team_id, self.team_dao)
        secondary = await get_team_by_id(secondary_team_id, self.team_dao)
        if primary.captain is None or primary.captain.id != captain.id:
            raise RequestPermissionError(player=captain, team=primary)
        existing = await self.requests.get_pending(
            type_=RequestType.team_merge, team_id=primary.id
        )
        if existing is not None:
            return existing
        payload = {
            "primary_team_id": primary.id,
            "primary_team_name": primary.name,
            "secondary_team_id": secondary.id,
            "secondary_team_name": secondary.name,
            "captain_id": captain.id,
            "captain_name": captain.name_mention,
        }
        request = await self.requests.create(
            type_=RequestType.team_merge,
            initiator_id=captain.id,
            team_id=primary.id,
            payload=payload,
        )
        await self.notifications.create_for_recipients(
            recipient_ids=await self.superusers.get_superuser_player_ids(),
            type_=NotificationType.team_merge_request,
            severity=NotificationSeverity.normal,
            actor_id=captain.id,
            payload=payload,
            request_id=request.id,
        )
        await self.notifier.notify_created(request)
        await self.requests.commit()
        return request


@dataclass
class CreatePlayerMergeRequestInteractor:
    """A player asks the admins to merge their achievements with a forum copy.

    An admin may also file the request on behalf of another player (``primary``
    differs from the actor), mirroring the old superuser-only bot command.
    """

    requests: RequestStorage
    notifications: NotificationWriter
    player_dao: PlayerByIdGetter
    superusers: SuperusersResolver
    notifier: RequestNotifier

    async def __call__(
        self,
        identity: IdentityProvider,
        secondary_player_id: int,
        primary_player_id: int | None = None,
    ) -> ndto.ActionRequest:
        actor = await identity.get_required_player()
        if primary_player_id is None or primary_player_id == actor.id:
            primary = actor
        else:
            await identity.get_superuser()
            primary = await self.player_dao.get_by_id(primary_player_id)
        secondary = await self.player_dao.get_by_id(secondary_player_id)
        existing = await self.requests.get_pending(
            type_=RequestType.player_merge, target_player_id=primary.id
        )
        if existing is not None:
            return existing
        payload = {
            "primary_player_id": primary.id,
            "primary_player_name": primary.name_mention,
            "secondary_player_id": secondary.id,
            "secondary_player_name": secondary.name_mention,
            "initiator_id": actor.id,
            "initiator_name": actor.name_mention,
        }
        request = await self.requests.create(
            type_=RequestType.player_merge,
            initiator_id=actor.id,
            target_player_id=primary.id,
            payload=payload,
        )
        await self.notifications.create_for_recipients(
            recipient_ids=await self.superusers.get_superuser_player_ids(),
            type_=NotificationType.player_merge_request,
            severity=NotificationSeverity.normal,
            actor_id=actor.id,
            payload=payload,
            request_id=request.id,
        )
        await self.notifier.notify_created(request)
        await self.requests.commit()
        return request


@dataclass
class AcceptRequestInteractor:
    requests: RequestStorage
    notifications: NotificationWriter
    team_joiner: TeamJoiner
    team_dao: TeamByIdGetter
    team_player_dao: TeamPlayerGetter
    player_dao: PlayerByIdGetter
    org_adder: OrgAdder
    team_merger: TeamMerger
    player_merger: PlayerMerger
    player_promoter: PlayerPromoter
    game_log: GameLogWriter
    team_notifier: TeamNotifier
    org_notifier: OrgNotifier
    bus: Bus

    async def __call__(
        self,
        identity: IdentityProvider,
        request_id: int,
        timeline: list[TimelineItem] | None = None,
    ) -> ndto.ActionRequest:
        """Accept the request.

        ``timeline`` only applies to player merge requests: when the players'
        team histories are not compatible, the admin passes a manually built
        history which replaces both (validated against the waiver points of
        both players).
        """
        actor = await identity.get_required_player()
        request = await self.requests.get_by_id(request_id)
        if not request.is_pending:
            raise RequestNotPending(player=actor)
        match request.type:
            case RequestType.team_join_invite:
                return await self._accept_team_join_invite(actor, request)
            case RequestType.team_join_request:
                return await self._accept_team_join_request(actor, request)
            case RequestType.org_invite:
                return await self._accept_org_invite(actor, request)
            case RequestType.team_merge:
                return await self._accept_team_merge(identity, request)
            case RequestType.player_merge:
                return await self._accept_player_merge(identity, request, timeline)
            case RequestType.promotion:
                return await self._accept_promotion(actor, request)
        raise RequestNotPending(player=actor)  # pragma: no cover - exhaustive match

    async def _accept_team_join_invite(
        self, actor: dto.Player, request: ndto.ActionRequest
    ) -> ndto.ActionRequest:
        if request.target_player_id != actor.id:
            raise RequestPermissionError(player=actor)
        assert request.team_id is not None
        manager = await self.player_dao.get_by_id(request.initiator_id)
        team = await get_team_by_id(request.team_id, self.team_dao)
        updated = await self._resolve(request, RequestStatus.accepted, actor)
        await self._notify_initiator(request, NotificationType.request_accepted, actor)
        await self._join(
            actor, team, manager, request.payload.get("role"), request.payload.get("emoji")
        )
        await self._submit_resolved(updated)
        return updated

    async def _accept_team_join_request(
        self, actor: dto.Player, request: ndto.ActionRequest
    ) -> ndto.ActionRequest:
        assert request.team_id is not None
        team = await get_team_by_id(request.team_id, self.team_dao)
        await check_can_add_players(actor, team, self.team_player_dao)
        joining = await self.player_dao.get_by_id(request.initiator_id)
        updated = await self._resolve(request, RequestStatus.accepted, actor)
        await self._notify_initiator(request, NotificationType.request_accepted, actor)
        await self._join(
            joining, team, actor, request.payload.get("role"), request.payload.get("emoji")
        )
        await self._submit_resolved(updated)
        return updated

    async def _accept_org_invite(
        self, actor: dto.Player, request: ndto.ActionRequest
    ) -> ndto.ActionRequest:
        if request.target_player_id != actor.id:
            raise RequestPermissionError(player=actor)
        assert request.game_id is not None
        game = await get_game(id_=request.game_id, dao=self.org_adder)
        notify_orgs = await get_orgs(game, self.org_adder)
        updated = await self._resolve(request, RequestStatus.accepted, actor)
        await self._notify_initiator(request, NotificationType.request_accepted, actor)
        org = await self.org_adder.add_new_org(game, actor)
        await self.requests.commit()
        await self.org_notifier.notify(NewOrg(orgs_list=notify_orgs, game=game, org=org))
        await self._submit_resolved(updated)
        return updated

    async def _accept_promotion(
        self, actor: dto.Player, request: ndto.ActionRequest
    ) -> ndto.ActionRequest:
        if request.target_player_id != actor.id:
            raise RequestPermissionError(player=actor)
        inviter = await self.player_dao.get_by_id(request.initiator_id)
        updated = await self._resolve(request, RequestStatus.accepted, actor)
        await self._notify_initiator(request, NotificationType.request_accepted, actor)
        # promote commits, taking the resolution and notification along
        await promote(inviter, actor, self.player_promoter)
        await self._submit_resolved(updated)
        return updated

    async def _accept_team_merge(
        self, identity: IdentityProvider, request: ndto.ActionRequest
    ) -> ndto.ActionRequest:
        admin = await identity.get_superuser()
        assert request.team_id is not None
        primary = await get_team_by_id(request.team_id, self.team_dao)
        secondary = await get_team_by_id(request.payload["secondary_team_id"], self.team_dao)
        captain = await self.player_dao.get_by_id(request.initiator_id)
        logger.warning(
            "admin %s accepted team merge request %s: merging team %s into %s",
            admin.id,
            request.id,
            secondary.id,
            primary.id,
        )
        updated = await self._resolve(request, RequestStatus.accepted, admin)
        await self._notify_initiator(request, NotificationType.request_accepted, admin)
        # merge_teams commits, taking the resolution and notification along
        await merge_teams(captain, primary, secondary, self.game_log, self.team_merger)
        await self._submit_resolved(updated)
        return updated

    async def _accept_player_merge(
        self,
        identity: IdentityProvider,
        request: ndto.ActionRequest,
        timeline: list[TimelineItem] | None = None,
    ) -> ndto.ActionRequest:
        admin = await identity.get_superuser()
        primary = await self.player_dao.get_by_id(request.payload["primary_player_id"])
        secondary = await self.player_dao.get_by_id(request.payload["secondary_player_id"])
        logger.warning(
            "admin %s accepted player merge request %s: merging player %s into %s%s",
            admin.id,
            request.id,
            secondary.id,
            primary.id,
            " with a custom timeline" if timeline is not None else "",
        )
        updated = await self._resolve(request, RequestStatus.accepted, admin)
        await self._notify_initiator(request, NotificationType.request_accepted, admin)
        # merge_players commits, taking the resolution and notification along
        await merge_players(primary, secondary, self.game_log, self.player_merger, timeline)
        await self._submit_resolved(updated)
        return updated

    async def _join(
        self,
        player: dto.Player,
        team: dto.Team,
        manager: dto.Player,
        role: str | None,
        emoji: str | None,
    ) -> None:
        with contextlib.suppress(PlayerRestoredInTeam):
            await join_team(
                player,
                team,
                manager,
                self.team_joiner,
                notifier=self.team_notifier,
                role=role or DEFAULT_ROLE,
                emoji=emoji,
            )

    async def _resolve(
        self, request: ndto.ActionRequest, status: RequestStatus, actor: dto.Player
    ) -> ndto.ActionRequest:
        return await self.requests.set_status(request.id, status, responder_id=actor.id)

    async def _submit_resolved(self, request: ndto.ActionRequest) -> None:
        await self.bus.submit(
            ActionRequestResolved(
                request_id=request.id,
            )
        )

    async def _notify_initiator(
        self, request: ndto.ActionRequest, type_: NotificationType, actor: dto.Player
    ) -> None:
        await self.notifications.create(
            recipient_id=request.initiator_id,
            type_=type_,
            severity=NotificationSeverity.normal,
            actor_id=actor.id,
            payload=request.payload,
            request_id=request.id,
        )


@dataclass
class DeclineRequestInteractor:
    requests: RequestStorage
    notifications: NotificationWriter
    team_dao: TeamByIdGetter
    team_player_dao: TeamPlayerGetter
    bus: Bus

    async def __call__(self, identity: IdentityProvider, request_id: int) -> ndto.ActionRequest:
        actor = await identity.get_required_player()
        request = await self.requests.get_by_id(request_id)
        if not request.is_pending:
            raise RequestNotPending(player=actor)
        await self._check_can_respond(identity, actor, request)
        if request.type in MERGE_REQUEST_TYPES:
            logger.warning(
                "admin %s declined %s request %s", actor.id, request.type.name, request.id
            )
        updated = await self.requests.set_status(
            request.id, RequestStatus.declined, responder_id=actor.id
        )
        await self.notifications.create(
            recipient_id=request.initiator_id,
            type_=NotificationType.request_declined,
            severity=NotificationSeverity.normal,
            actor_id=actor.id,
            payload=request.payload,
            request_id=request.id,
        )
        await self.requests.commit()
        await self.bus.submit(
            ActionRequestResolved(
                request_id=updated.id,
            )
        )
        return updated

    async def _check_can_respond(
        self, identity: IdentityProvider, actor: dto.Player, request: ndto.ActionRequest
    ) -> None:
        if request.type == RequestType.team_join_request:
            assert request.team_id is not None
            team = await get_team_by_id(request.team_id, self.team_dao)
            await check_can_add_players(actor, team, self.team_player_dao)
        elif request.type in MERGE_REQUEST_TYPES:
            # the player whose account would be merged may refuse; otherwise only admins
            if request.type == RequestType.player_merge and request.target_player_id == actor.id:
                return
            await identity.get_superuser()
        elif request.target_player_id != actor.id:
            raise RequestPermissionError(player=actor)


@dataclass
class CancelRequestInteractor:
    """The initiator withdraws their own pending request."""

    requests: RequestStorage
    bus: Bus

    async def __call__(self, identity: IdentityProvider, request_id: int) -> ndto.ActionRequest:
        actor = await identity.get_required_player()
        request = await self.requests.get_by_id(request_id)
        if not request.is_pending:
            raise RequestNotPending(player=actor)
        if request.initiator_id != actor.id:
            raise RequestPermissionError(player=actor)
        updated = await self.requests.set_status(
            request.id, RequestStatus.cancelled, responder_id=actor.id
        )
        await self.requests.commit()
        await self.bus.submit(
            ActionRequestResolved(
                request_id=updated.id,
            )
        )
        return updated


@dataclass
class ListRequestsInteractor:
    requests: RequestStorage

    async def incoming(
        self, identity: IdentityProvider, *, only_pending: bool = False
    ) -> Sequence[ndto.ActionRequest]:
        player = await identity.get_required_player()
        result = list(await self.requests.get_incoming(player.id, only_pending=only_pending))
        team = await identity.get_team()
        if team is not None:
            # team managers also answer un-targeted join requests for their team
            result.extend(await self.requests.get_pending_for_teams([team.id]))
        if await identity.is_superuser():
            # admins answer merge requests, which target no particular player
            seen = {request.id for request in result}
            result.extend(
                request
                for request in await self.requests.get_pending_by_types(MERGE_REQUEST_TYPES)
                if request.id not in seen
            )
        return result

    async def outgoing(
        self, identity: IdentityProvider, *, only_pending: bool = False
    ) -> Sequence[ndto.ActionRequest]:
        player = await identity.get_required_player()
        return await self.requests.get_outgoing(player.id, only_pending=only_pending)
