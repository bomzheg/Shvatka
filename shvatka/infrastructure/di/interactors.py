from aiogram import Bot
from adaptix import Retort
from dishka import Provider, Scope, provide

from shvatka.common import Config
from shvatka.common.url_factory import UrlFactory
from shvatka.core.games.interactors import (
    GameFileReaderInteractor,
    GamePlayReaderInteractor,
    GameKeysReaderInteractor,
    GameStatReaderInteractor,
    GameResultsFileInteractor,
    GamePlayTimerInteractor,
    CheckKeyInteractor,
    GamePlayRoleReader,
)
from shvatka.core.games.editor_interactors import (
    MyGamesInteractor,
    MyGameInteractor,
    CreateGameInteractor,
    ChangeGameScenarioInteractor,
    PlanGameStartInteractor,
    ChangeGameStatusInteractor,
    UploadGameFileInteractor,
    RenameGameFileInteractor,
)
from shvatka.core.games.admin_interactors import (
    AdminUpdateGameScenarioInteractor,
    AdminUploadGameFileInteractor,
)
from shvatka.core.games.adapters import AdminGameScenarioEditor
from shvatka.core.games.org_interactors import (
    ListGameOrgsInteractor,
    AddGameOrgInteractor,
    ChangeOrgPermissionInteractor,
    RemoveGameOrgInteractor,
)
from shvatka.core.notifications.interactors import (
    ListNotificationsInteractor,
    UnreadCountInteractor,
    MarkNotificationsReadInteractor,
    MarkAllNotificationsReadInteractor,
)
from shvatka.core.notifications.request_interactors import (
    CreateTeamJoinInviteInteractor,
    CreateTeamJoinRequestInteractor,
    CreateOrgInviteInteractor,
    CreatePromotionInviteInteractor,
    CreateTeamMergeRequestInteractor,
    CreatePlayerMergeRequestInteractor,
    AcceptRequestInteractor,
    DeclineRequestInteractor,
    CancelRequestInteractor,
    ListRequestsInteractor,
)
from shvatka.core.interfaces.superusers import SuperusersResolver
from shvatka.core.notifications.adapters import (
    RequestNotifier,
    RequestStorage,
    NotificationWriter,
)
from shvatka.tgbot.config.models.bot import BotConfig
from shvatka.tgbot.services.action_requests import ActionResolvedInteractorImpl
from shvatka.tgbot.views.action_request import BotRequestNotifier
from shvatka.core.players.interactors import (
    GetPlayerInteractor,
    GetPlayerStatInteractor,
    SearchPlayersInteractor,
)
from shvatka.core.players.admin_interactors import (
    AdminSetPlayerEmailInteractor,
    AdminChangePlayerTgInteractor,
    AdminMergePlayersInteractor,
    AdminSearchPlayersInteractor,
    AdminGetPlayerInteractor,
    AdminGetPlayerWaiverPointsInteractor,
)
from shvatka.core.players.interfaces import (
    AdminPlayerReader,
    AdminEmailSetter,
    AdminTgChanger,
    AdminPlayerMerger,
    AdminPlayerWaiverPointsReader,
)
from shvatka.core.teams.admin_interactors import AdminMergeTeamsInteractor
from shvatka.core.services.one_time_link import (
    GenerateOneTimeLoginLinkInteractor,
    GenerateOneTimeLoginLinkForPlayerInteractor,
)
from shvatka.core.waiver.admin_interactors import (
    AdminPollReaderInteractor,
    AdminRemovePollVoteInteractor,
    AdminGameWaiversReaderInteractor,
)
from shvatka.core.teams.interactors import (
    AddPlayerToTeamInteractor,
    CreateTeamInteractor,
    EditTeamInteractor,
    GetTeamInteractor,
    RemovePlayerFromTeamInteractor,
    TeamPlayedGamesInteractor,
    TeamPlayersInteractor,
    TeamsListInteractor,
    UpdateTeamPlayerInteractor,
)
from shvatka.core.teams.adapters import ChatlessTeamCreator, AdminTeamMerger
from shvatka.core.views.game import GameLogWriter, OrgNotifier
from shvatka.core.views.team import TeamNotifier
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.interfaces.dal.complex import GameScenarioEditor
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.games.adapters import (
    GameFileReader,
    GameKeysReader,
    GameStatReader,
    GamePlayDao,
)
from shvatka.core.interfaces.bus import Bus
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.dal.game import GameByIdGetter, GameFileRenamer, GameFileUploader
from shvatka.core.interfaces.dal.game_play import GamePlayerDao
from shvatka.core.services.current_game import CurrentGameProviderImpl
from shvatka.core.interfaces.dal.waiver import WaiverApprover
from shvatka.core.waiver.adapters import (
    WaiverVoteAdder,
    WaiverVoteGetter,
    PollDraftsReader,
    PollVoteRemover,
    AdminPollReader,
    AdminGameWaiversReader,
)
from shvatka.core.scenario.interactors import (
    AllGameKeysReaderInteractor,
    GameScenarioTransitionsInteractor,
)
from shvatka.core.search.adapters import GlobalSearchDao
from shvatka.core.search.interactors import GlobalSearchInteractor
from shvatka.core.services.key import KeyProcessor, TimerProcessor
from shvatka.core.waiver.interactors import (
    TeamWaiversDraftReaderInteractor,
    AddWaiverVoteInteractor,
    WaiverCompleteReaderInteractor,
    AllWaiversDraftReaderInteractor,
    ReplaceTeamWaiversInteractor,
)
from shvatka.infrastructure.bus.in_memory import ActionResolvedInteractor, InMemoryBus
from shvatka.infrastructure.superusers import ConfigSuperusersResolver
from shvatka.infrastructure.db.dao.complex2.waiver import (
    WaiverVoteAdderImpl,
    WaiverVoteGetterImpl,
    PollDraftsReaderImpl,
    AdminPollReaderImpl,
    PollVoteRemoverImpl,
    AdminGameWaiversReaderImpl,
)
from shvatka.infrastructure.db.dao.complex.player import (
    AdminEmailSetterImpl,
    AdminTgChangerImpl,
    AdminPlayerMergerImpl,
    AdminPlayerReaderImpl,
    AdminPlayerWaiverPointsReaderImpl,
)
from shvatka.infrastructure.db.dao.complex.game import (
    AdminGameScenarioEditorImpl,
    GameFilesGetterImpl,
    GameScenarioEditorImpl,
)
from shvatka.infrastructure.db.dao.complex.game import (
    GameFileRenamerImpl,
    GameFileUploaderImpl,
    GamePlayDaoImpl,
)
from shvatka.infrastructure.db.dao.complex.game_play import GamePlayerDaoImpl
from shvatka.infrastructure.db.dao.complex.team import TeamCreatorImpl, AdminTeamMergerImpl
from shvatka.infrastructure.db.dao.complex.key_log import GameKeysReaderImpl
from shvatka.infrastructure.db.dao.complex.level_times import GameStatReaderImpl
from shvatka.infrastructure.db.dao.complex.search import GlobalSearchDaoImpl
from shvatka.infrastructure.db.dao.holder import HolderDao


class ContextProvider(Provider):
    scope = Scope.REQUEST
    current_game = provide(CurrentGameProviderImpl, provides=CurrentGameProvider)
    bus = provide(InMemoryBus, provides=Bus)
    action_resolved = provide(ActionResolvedInteractorImpl, provides=ActionResolvedInteractor)

    @provide
    def request_notifier(
        self, bot: Bot, dao: HolderDao, requests: RequestStorage, bot_config: BotConfig
    ) -> RequestNotifier:
        return BotRequestNotifier(
            bot=bot,
            requests=requests,
            player_dao=dao.player,
            team_dao=dao.team,
            team_players_dao=dao.team_player,
            game_log_chat=bot_config.game_log_chat,
        )

    @provide
    def superusers_resolver(self, config: Config, dao: HolderDao) -> SuperusersResolver:
        return ConfigSuperusersResolver(config=config, player_dao=dao.player)


class GamePlayProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_game_keys(self, dao: HolderDao) -> GameKeysReader:
        return GameKeysReaderImpl(dao)

    get_game_keys_interactor = provide(GameKeysReaderInteractor)

    @provide
    def get_game_state(self, dao: HolderDao) -> GameStatReader:
        return GameStatReaderImpl(dao)

    get_game_state_interactor = provide(GameStatReaderInteractor)
    get_game_results_file_interactor = provide(GameResultsFileInteractor)

    @provide
    def get_game_files(self, dao: HolderDao) -> GameFileReader:
        return GameFilesGetterImpl(dao)

    file_reader = provide(GameFileReaderInteractor)
    game_play_reader_interactor = provide(GamePlayReaderInteractor)

    @provide
    def game_play_dao(self, dao: HolderDao, current_game: CurrentGameProvider) -> GamePlayDao:
        return GamePlayDaoImpl(dao=dao, current_game=current_game, cache={})

    @provide
    def game_player_dao(self, dao: HolderDao) -> GamePlayerDao:
        return GamePlayerDaoImpl(dao)

    game_play_role_reader = provide(GamePlayRoleReader)

    check_key_interactor = provide(CheckKeyInteractor)
    key_processor = provide(KeyProcessor)
    timer_event_interactor = provide(GamePlayTimerInteractor)
    timer_processor = provide(TimerProcessor)

    @provide
    def game_by_id_getter(self, dao: HolderDao) -> GameByIdGetter:
        return dao.game

    all_game_keys_reader_interactor = provide(AllGameKeysReaderInteractor)
    transitions_reader_interactor = provide(GameScenarioTransitionsInteractor)


class GameEditProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def my_games(self, dao: HolderDao) -> MyGamesInteractor:
        return MyGamesInteractor(dao.game)

    @provide
    def my_game(self, dao: HolderDao) -> MyGameInteractor:
        return MyGameInteractor(dao.game)

    @provide
    def create_game(self, dao: HolderDao) -> CreateGameInteractor:
        return CreateGameInteractor(dao.game_creator)

    @provide
    def game_scenario_editor(self, dao: HolderDao) -> GameScenarioEditor:
        return GameScenarioEditorImpl(dao=dao)

    @provide
    def change_scenario(
        self, dao: GameScenarioEditor, retort: Retort
    ) -> ChangeGameScenarioInteractor:
        return ChangeGameScenarioInteractor(dao=dao, retort=retort)

    @provide
    def change_start_at(
        self, dao: HolderDao, scheduler: Scheduler, game_log: GameLogWriter
    ) -> PlanGameStartInteractor:
        return PlanGameStartInteractor(
            getter=dao.game, dao=dao.game, scheduler=scheduler, game_log=game_log
        )

    @provide
    def change_status(self, dao: HolderDao, game_log: GameLogWriter) -> ChangeGameStatusInteractor:
        return ChangeGameStatusInteractor(
            getter=dao.game, waiver_starter=dao.game, completer=dao.game, game_log=game_log
        )

    @provide
    def game_file_uploader(self, dao: HolderDao) -> GameFileUploader:
        return GameFileUploaderImpl(dao=dao)

    @provide
    def upload_file(self, dao: GameFileUploader, storage: FileStorage) -> UploadGameFileInteractor:
        return UploadGameFileInteractor(storage=storage, dao=dao)

    @provide
    def game_file_renamer(self, dao: HolderDao) -> GameFileRenamer:
        return GameFileRenamerImpl(dao=dao)

    @provide
    def rename_file(self, dao: GameFileRenamer) -> RenameGameFileInteractor:
        return RenameGameFileInteractor(dao=dao)

    @provide
    def list_orgs(self, dao: HolderDao) -> ListGameOrgsInteractor:
        return ListGameOrgsInteractor(game_dao=dao.game, org_dao=dao.organizer)

    @provide
    def add_org(self, dao: HolderDao) -> AddGameOrgInteractor:
        return AddGameOrgInteractor(
            game_dao=dao.game,
            player_dao=dao.player,
            org_getter=dao.organizer,
            org_adder=dao.org_adder,
            org_deleted_flipper=dao.organizer,
        )

    @provide
    def change_org_permission(self, dao: HolderDao) -> ChangeOrgPermissionInteractor:
        return ChangeOrgPermissionInteractor(game_dao=dao.game, org_dao=dao.organizer)

    @provide
    def remove_org(self, dao: HolderDao) -> RemoveGameOrgInteractor:
        return RemoveGameOrgInteractor(game_dao=dao.game, org_dao=dao.organizer)


class WaiverProvider(Provider):
    scope = Scope.REQUEST

    waivers_reader_interactor = provide(TeamWaiversDraftReaderInteractor)
    add_waiver_vote = provide(AddWaiverVoteInteractor)
    waivers_complete_reader_interactor = provide(WaiverCompleteReaderInteractor)
    waiver_draft_reader_interactor = provide(AllWaiversDraftReaderInteractor)
    replace_team_waivers_interactor = provide(ReplaceTeamWaiversInteractor)

    waiver_vote_adder_dao = provide(WaiverVoteAdderImpl, provides=WaiverVoteAdder)
    waiver_vote_getter_dao = provide(WaiverVoteGetterImpl, provides=WaiverVoteGetter)
    poll_drafts_reader_dao = provide(PollDraftsReaderImpl, provides=PollDraftsReader)

    @provide
    def waiver_approver(self, dao: HolderDao) -> WaiverApprover:
        return dao.waiver_approver


class PlayerProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_player(self, dao: HolderDao) -> GetPlayerInteractor:
        return GetPlayerInteractor(player_dao=dao.player, team_player_dao=dao.team_player)

    @provide
    def search_players(self, dao: HolderDao) -> SearchPlayersInteractor:
        return SearchPlayersInteractor(dao=dao.player)

    @provide
    def get_player_stat(self, dao: HolderDao) -> GetPlayerStatInteractor:
        return GetPlayerStatInteractor(
            player_dao=dao.player,
            history_dao=dao.team_player,
            played_games_dao=dao.player,
        )

    @provide
    def get_otl_link_interactor(
        self, dao: HolderDao, url_factory: UrlFactory
    ) -> GenerateOneTimeLoginLinkInteractor:
        return GenerateOneTimeLoginLinkInteractor(
            token_creator=dao.one_time_token,
            url_factory=url_factory,
        )


class TeamProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_teams(self, dao: HolderDao) -> TeamsListInteractor:
        return TeamsListInteractor(dao=dao.team)

    @provide
    def get_team(self, dao: HolderDao) -> GetTeamInteractor:
        return GetTeamInteractor(dao=dao.team)

    @provide
    def get_team_stat(self, dao: HolderDao) -> TeamPlayedGamesInteractor:
        return TeamPlayedGamesInteractor(team_dao=dao.team, played_games_dao=dao.team)

    @provide
    def get_team_players(self, dao: HolderDao) -> TeamPlayersInteractor:
        return TeamPlayersInteractor(
            team_dao=dao.team, players_dao=dao.team_player, counter=dao.player
        )

    @provide
    def add_player(self, dao: HolderDao, notifier: TeamNotifier) -> AddPlayerToTeamInteractor:
        return AddPlayerToTeamInteractor(
            dao=dao.team_player, team_dao=dao.team, player_dao=dao.player, notifier=notifier
        )

    @provide
    def remove_player(
        self, dao: HolderDao, notifier: TeamNotifier
    ) -> RemovePlayerFromTeamInteractor:
        return RemovePlayerFromTeamInteractor(
            dao=dao.team_leaver, player_dao=dao.player, notifier=notifier
        )

    @provide
    def update_team_player(self, dao: HolderDao) -> UpdateTeamPlayerInteractor:
        return UpdateTeamPlayerInteractor(
            dao=dao.team_player, team_dao=dao.team, player_dao=dao.player
        )

    @provide
    def edit_team(self, dao: HolderDao) -> EditTeamInteractor:
        return EditTeamInteractor(dao=dao.team, team_player_dao=dao.team_player)

    @provide
    def chatless_team_creator(self, dao: HolderDao) -> ChatlessTeamCreator:
        return TeamCreatorImpl(dao=dao)

    @provide
    def create_team(
        self, dao: ChatlessTeamCreator, game_log: GameLogWriter
    ) -> CreateTeamInteractor:
        return CreateTeamInteractor(dao=dao, game_log=game_log)


class SearchProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def global_search_dao(self, dao: HolderDao) -> GlobalSearchDao:
        return GlobalSearchDaoImpl(dao)

    global_search = provide(GlobalSearchInteractor)


class AdminProvider(Provider):
    scope = Scope.REQUEST

    # DAO adapters. complex2/waiver impls import HolderDao directly, so dishka can
    # analyse the class-provide shorthand. complex/player and complex/team impls
    # import HolderDao under TYPE_CHECKING (to break a circular import), so they
    # need an explicit factory instead.
    admin_poll_reader_dao = provide(AdminPollReaderImpl, provides=AdminPollReader)
    poll_vote_remover_dao = provide(PollVoteRemoverImpl, provides=PollVoteRemover)
    admin_waivers_reader_dao = provide(AdminGameWaiversReaderImpl, provides=AdminGameWaiversReader)

    @provide
    def admin_email_setter(self, dao: HolderDao) -> AdminEmailSetter:
        return AdminEmailSetterImpl(dao)

    @provide
    def admin_tg_changer(self, dao: HolderDao) -> AdminTgChanger:
        return AdminTgChangerImpl(dao)

    @provide
    def admin_player_reader(self, dao: HolderDao) -> AdminPlayerReader:
        return AdminPlayerReaderImpl(dao)

    @provide
    def admin_player_merger_dao(self, dao: HolderDao) -> AdminPlayerMerger:
        return AdminPlayerMergerImpl(dao)

    @provide
    def admin_player_waiver_points_dao(self, dao: HolderDao) -> AdminPlayerWaiverPointsReader:
        return AdminPlayerWaiverPointsReaderImpl(dao)

    @provide
    def admin_team_merger_dao(self, dao: HolderDao) -> AdminTeamMerger:
        return AdminTeamMergerImpl(dao)

    # Interactors
    admin_set_email = provide(AdminSetPlayerEmailInteractor)
    admin_change_tg = provide(AdminChangePlayerTgInteractor)
    admin_get_player = provide(AdminGetPlayerInteractor)
    admin_poll_reader = provide(AdminPollReaderInteractor)
    admin_remove_poll_vote = provide(AdminRemovePollVoteInteractor)
    admin_merge_players = provide(AdminMergePlayersInteractor)
    admin_player_waiver_points = provide(AdminGetPlayerWaiverPointsInteractor)
    admin_merge_teams = provide(AdminMergeTeamsInteractor)
    admin_waivers_reader = provide(AdminGameWaiversReaderInteractor)

    @provide
    def admin_search_players(self, dao: HolderDao) -> AdminSearchPlayersInteractor:
        return AdminSearchPlayersInteractor(dao=dao.player)

    admin_update_scenario = provide(AdminUpdateGameScenarioInteractor)
    admin_upload_file = provide(AdminUploadGameFileInteractor)

    @provide
    def admin_game_scenario_editor(self, dao: HolderDao) -> AdminGameScenarioEditor:
        return AdminGameScenarioEditorImpl(dao=dao)

    @provide
    def admin_otl(
        self, dao: HolderDao, url_factory: UrlFactory
    ) -> GenerateOneTimeLoginLinkForPlayerInteractor:
        return GenerateOneTimeLoginLinkForPlayerInteractor(
            player_getter=dao.player,
            token_creator=dao.one_time_token,
            url_factory=url_factory,
        )


class NotificationProvider(Provider):
    scope = Scope.REQUEST

    list_notifications = provide(ListNotificationsInteractor)
    unread_count = provide(UnreadCountInteractor)
    mark_read = provide(MarkNotificationsReadInteractor)
    mark_all_read = provide(MarkAllNotificationsReadInteractor)


class RequestProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def create_team_join_invite(
        self,
        dao: HolderDao,
        requests: RequestStorage,
        notifications: NotificationWriter,
        notifier: RequestNotifier,
    ) -> CreateTeamJoinInviteInteractor:
        return CreateTeamJoinInviteInteractor(
            requests=requests,
            notifications=notifications,
            team_dao=dao.team,
            player_dao=dao.player,
            team_player_dao=dao.team_player,
            notifier=notifier,
        )

    @provide
    def create_team_join_request(
        self,
        dao: HolderDao,
        requests: RequestStorage,
        notifications: NotificationWriter,
        notifier: RequestNotifier,
    ) -> CreateTeamJoinRequestInteractor:
        return CreateTeamJoinRequestInteractor(
            requests=requests,
            notifications=notifications,
            team_dao=dao.team,
            team_players_dao=dao.team_player,
            notifier=notifier,
        )

    @provide
    def create_org_invite(
        self,
        dao: HolderDao,
        requests: RequestStorage,
        notifications: NotificationWriter,
        notifier: RequestNotifier,
    ) -> CreateOrgInviteInteractor:
        return CreateOrgInviteInteractor(
            requests=requests,
            notifications=notifications,
            player_dao=dao.player,
            org_adder=dao.org_adder,
            notifier=notifier,
        )

    @provide
    def create_promotion_invite(
        self,
        dao: HolderDao,
        requests: RequestStorage,
        notifications: NotificationWriter,
        notifier: RequestNotifier,
    ) -> CreatePromotionInviteInteractor:
        return CreatePromotionInviteInteractor(
            requests=requests,
            notifications=notifications,
            player_dao=dao.player,
            notifier=notifier,
        )

    @provide
    def create_team_merge_request(
        self,
        dao: HolderDao,
        requests: RequestStorage,
        notifications: NotificationWriter,
        superusers: SuperusersResolver,
        notifier: RequestNotifier,
    ) -> CreateTeamMergeRequestInteractor:
        return CreateTeamMergeRequestInteractor(
            requests=requests,
            notifications=notifications,
            team_dao=dao.team,
            superusers=superusers,
            notifier=notifier,
        )

    @provide
    def create_player_merge_request(
        self,
        dao: HolderDao,
        requests: RequestStorage,
        notifications: NotificationWriter,
        superusers: SuperusersResolver,
        notifier: RequestNotifier,
    ) -> CreatePlayerMergeRequestInteractor:
        return CreatePlayerMergeRequestInteractor(
            requests=requests,
            notifications=notifications,
            player_dao=dao.player,
            superusers=superusers,
            notifier=notifier,
        )

    @provide
    def accept_request(
        self,
        dao: HolderDao,
        requests: RequestStorage,
        notifications: NotificationWriter,
        team_notifier: TeamNotifier,
        org_notifier: OrgNotifier,
        game_log: GameLogWriter,
        bus: Bus,
    ) -> AcceptRequestInteractor:
        return AcceptRequestInteractor(
            requests=requests,
            notifications=notifications,
            team_joiner=dao.team_player,
            team_dao=dao.team,
            team_player_dao=dao.team_player,
            player_dao=dao.player,
            org_adder=dao.org_adder,
            team_merger=dao.team_merger,
            player_merger=dao.player_merger,
            player_promoter=dao.player_promoter,
            game_log=game_log,
            team_notifier=team_notifier,
            org_notifier=org_notifier,
            bus=bus,
        )

    @provide
    def decline_request(
        self, dao: HolderDao, requests: RequestStorage, notifications: NotificationWriter, bus: Bus
    ) -> DeclineRequestInteractor:
        return DeclineRequestInteractor(
            requests=requests,
            notifications=notifications,
            team_dao=dao.team,
            team_player_dao=dao.team_player,
            bus=bus,
        )

    @provide
    def cancel_request(self, requests: RequestStorage, bus: Bus) -> CancelRequestInteractor:
        return CancelRequestInteractor(requests=requests, bus=bus)

    @provide
    def list_requests(self, requests: RequestStorage) -> ListRequestsInteractor:
        return ListRequestsInteractor(requests=requests)
