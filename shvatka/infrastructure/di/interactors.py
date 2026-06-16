from adaptix import Retort
from dishka import Provider, Scope, provide

from shvatka.core.games.interactors import (
    GameFileReaderInteractor,
    GamePlayReaderInteractor,
    GameKeysReaderInteractor,
    GameStatReaderInteractor,
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
)
from shvatka.core.games.org_interactors import (
    ListGameOrgsInteractor,
    AddGameOrgInteractor,
    ChangeOrgPermissionInteractor,
    RemoveGameOrgInteractor,
)
from shvatka.core.players.interactors import (
    GetPlayerInteractor,
    SearchPlayersInteractor,
)
from shvatka.core.teams.interactors import (
    AddPlayerToTeamInteractor,
    EditTeamInteractor,
    GetTeamInteractor,
    RemovePlayerFromTeamInteractor,
    TeamPlayersInteractor,
    TeamsListInteractor,
    UpdateTeamPlayerInteractor,
)
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
from shvatka.core.interfaces.dal.game import GameByIdGetter
from shvatka.core.interfaces.dal.game_play import GamePlayerDao
from shvatka.core.services.current_game import CurrentGameProviderImpl
from shvatka.core.interfaces.dal.waiver import WaiverApprover
from shvatka.core.waiver.adapters import WaiverVoteAdder, WaiverVoteGetter, PollDraftsReader
from shvatka.core.scenario.interactors import (
    AllGameKeysReaderInteractor,
    GameScenarioTransitionsInteractor,
)
from shvatka.core.services.key import KeyProcessor, TimerProcessor
from shvatka.core.waiver.interactors import (
    TeamWaiversDraftReaderInteractor,
    AddWaiverVoteInteractor,
    WaiverCompleteReaderInteractor,
    AllWaiversDraftReaderInteractor,
    ReplaceTeamWaiversInteractor,
)
from shvatka.infrastructure.bus.in_memory import InMemoryBus
from shvatka.infrastructure.db.dao.complex2.waiver import (
    WaiverVoteAdderImpl,
    WaiverVoteGetterImpl,
    PollDraftsReaderImpl,
)
from shvatka.infrastructure.db.dao.complex.game import GameFilesGetterImpl, GameScenarioEditorImpl
from shvatka.infrastructure.db.dao.complex.game import (
    GamePlayDaoImpl,
)
from shvatka.infrastructure.db.dao.complex.game_play import GamePlayerDaoImpl
from shvatka.infrastructure.db.dao.complex.key_log import GameKeysReaderImpl
from shvatka.infrastructure.db.dao.complex.level_times import GameStatReaderImpl
from shvatka.infrastructure.db.dao.holder import HolderDao


class ContextProvider(Provider):
    scope = Scope.REQUEST
    current_game = provide(CurrentGameProviderImpl, provides=CurrentGameProvider)
    bus = provide(InMemoryBus, provides=Bus)


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
    def change_start_at(self, dao: HolderDao, scheduler: Scheduler) -> PlanGameStartInteractor:
        return PlanGameStartInteractor(getter=dao.game, dao=dao.game, scheduler=scheduler)

    @provide
    def change_status(self, dao: HolderDao) -> ChangeGameStatusInteractor:
        return ChangeGameStatusInteractor(
            getter=dao.game, waiver_starter=dao.game, completer=dao.game
        )

    @provide
    def upload_file(self, dao: HolderDao, storage: FileStorage) -> UploadGameFileInteractor:
        return UploadGameFileInteractor(storage=storage, game_dao=dao.game, file_dao=dao.file_info)

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


class TeamProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_teams(self, dao: HolderDao) -> TeamsListInteractor:
        return TeamsListInteractor(dao=dao.team)

    @provide
    def get_team(self, dao: HolderDao) -> GetTeamInteractor:
        return GetTeamInteractor(dao=dao.team)

    @provide
    def get_team_players(self, dao: HolderDao) -> TeamPlayersInteractor:
        return TeamPlayersInteractor(team_dao=dao.team, players_dao=dao.team_player)

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
