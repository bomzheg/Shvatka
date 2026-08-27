import logging
import typing
from dataclasses import dataclass
from datetime import datetime

from shvatka.core.games.dto import (
    CurrentHintsAndKeys,
    GameStatWithBonuses,
    MyRole,
    PassedLevels,
)
from shvatka.core.games.game_play import schedule_first_hint
from shvatka.core.games.results import build_results_table, resolve_bonus_levels
from shvatka.core.interfaces.clients.file_storage import FileGateway
from shvatka.core.interfaces.printer import TablePrinter
from shvatka.core.games.adapters import (
    GameFileReader,
    GameKeysReader,
    GameStatReader,
    GamePlayDao,
)
from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.dal.game_play import GamePlayerDao
from shvatka.core.interfaces.dal.organizer import OrgByPlayerGetter
from shvatka.core.interfaces.dal.waiver import WaiverGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.scheduler import Scheduler
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import action
from shvatka.core.models.dto.hints import VerifiableFileMeta
from shvatka.core.services.game_stat import (
    get_typed_keys,
    get_game_stat,
    get_game_stat_with_hints,
)
from shvatka.core.services.key import TimerProcessor, KeyProcessor
from shvatka.core.services.organizers import get_spying_orgs, get_by_player_or_none
from shvatka.core.utils import exceptions
from shvatka.core.utils.datetime_utils import tz_utc
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory
from shvatka.core.views.game import (
    AnyViewTask,
    DuplicateKey,
    EffectsKey,
    GameFinished,
    GameFinishedByAll,
    InputContainer,
    LevelUp,
    GameLogEvent,
    GameLogType,
    SendPuzzle,
    ShowEffects,
    ShowTasks,
    ViewSender,
    WrongKey,
)
from shvatka.infrastructure.scheduler import SchedulerContainer


logger = logging.getLogger(__name__)


class GameKeysReaderInteractor:
    def __init__(self, dao: GameKeysReader):
        self.dao = dao

    async def __call__(
        self, game_id: int, identity: IdentityProvider
    ) -> dict[int, list[dto.KeyTime]]:
        game = await self.dao.get_by_id(game_id)
        keys = await get_typed_keys(game, identity, self.dao)
        return {t.id: k for t, k in keys.items()}


class GameStatReaderInteractor:
    def __init__(self, dao: GameStatReader):
        self.dao = dao

    async def __call__(self, game_id: int, identity: IdentityProvider) -> GameStatWithBonuses:
        player = await identity.get_required_player()
        game = await self.dao.get_by_id(game_id)
        stat = await get_game_stat_with_hints(game, player, self.dao)
        bonuses = await self.dao.get_game_bonuses_by_teams(game)
        return GameStatWithBonuses(
            level_times=stat.level_times,
            bonuses={
                team.id: resolve_bonus_levels(lts, bonuses[team.id])
                for team, lts in stat.level_times.items()
                if bonuses.get(team.id)
            },
        )


class GameResultsFileInteractor:
    def __init__(self, dao: GameStatReader, printer: TablePrinter):
        self.dao = dao
        self.printer = printer

    async def __call__(self, game_id: int, identity: IdentityProvider) -> typing.BinaryIO:
        game = await self.dao.get_full(game_id)
        game_stat = await get_game_stat(game, identity, self.dao)
        bonuses = await self.dao.get_game_bonuses_by_teams(game)
        return self.printer.print_table(build_results_table(game, game_stat, bonuses))


class GameFileReaderInteractor:
    def __init__(
        self,
        dao: GameFileReader,
        file_gateway: FileGateway,
        current_game: CurrentGameProvider,
        game_play_dao: GamePlayDao,
        org_dao: OrgByPlayerGetter,
    ):
        self.file_gateway = file_gateway
        self.dao = dao
        self.current_game = current_game
        self.game_play_dao = game_play_dao
        self.org_dao = org_dao

    async def __call__(
        self, guid: str, game_id: int, identity: IdentityProvider
    ) -> VerifiableFileMeta:
        if await self.is_guid_in_release(game_id, guid):
            # a release is promo: its banner is public, even for guests
            return await self.dao.get_by_guid(guid)
        player = await identity.get_required_player()
        game = await self.dao.get_full(game_id)
        if (
            game.author.id == player.id
            or game.is_complete()
            or await self.can_view_scenario(game, player)
        ):
            if not await self.dao.is_game_file(game_id, guid):
                raise exceptions.FileNotFound(
                    text=f"There is no file with uuid {guid} associated with game id {game_id}",
                    game=game,
                    user=await identity.get_user(),
                    player=player,
                )
        elif game.is_started():
            if not await self.is_guid_available_to_team(identity, guid):
                raise exceptions.NotAuthorizedForEdit(
                    permission_name="game_file_read",
                    text=f"There is no file with uuid {guid} associated "
                    f"with game id {game_id} and available now",
                    game=game,
                    user=await identity.get_user(),
                    player=player,
                )
        else:
            raise exceptions.NotAuthorizedForEdit(
                permission_name="game_file_read",
                player=player,
                game=game,
                user=await identity.get_user(),
            )

        meta = await self.dao.get_by_guid(guid)
        return meta

    async def can_view_scenario(self, game: dto.Game, player: dto.Player) -> bool:
        org = await self.org_dao.get_by_player_or_none(game=game, player=player)
        return org is not None and not org.deleted and org.view_scenario

    async def is_guid_in_release(self, game_id: int, guid: str) -> bool:
        release = await self.dao.get_release(game_id)
        if release is None:
            return False
        return guid in release.get_guids()

    async def is_guid_available_to_team(self, identity: IdentityProvider, guid: str) -> bool:
        """Whether the team has already been shown the file.

        A hint the team saw stays readable after it left the level — that's
        what makes the passed levels browsable — but a hint it never reached
        does not become readable by passing the level.
        """
        return (
            await self.is_guid_in_current_hint(identity, guid)
            or await self.is_guid_in_applied_effects(identity, guid)
            or await self.is_guid_in_passed_levels(identity, guid)
        )

    async def is_guid_in_current_hint(self, identity: IdentityProvider, guid: str) -> bool:
        hints_ = await self.game_play_dao.get_current_hints(identity)
        return guid in hints_.get_guids()

    async def is_guid_in_passed_levels(self, identity: IdentityProvider, guid: str) -> bool:
        passed = await self.game_play_dao.get_passed_levels(identity)
        return guid in passed.get_guids()

    async def is_guid_in_applied_effects(self, identity: IdentityProvider, guid: str) -> bool:
        effects = await self.game_play_dao.get_effects(identity)
        guids = {g for e in effects for g in e.effects.get_guids()}
        return guid in guids


@dataclass(kw_only=True, slots=True, frozen=True)
class GamePlayRoleReader:
    current_game: CurrentGameProvider
    waiver_dao: WaiverGetter
    org_dao: OrgByPlayerGetter

    async def __call__(self, identity: IdentityProvider) -> MyRole:
        game = await self.current_game.get_required_game()
        team = await identity.get_team()
        player = await identity.get_player()
        if team is not None and player is not None:
            waiver = await self.waiver_dao.get_player_waiver(player=player, team=team, game=game)
            played = waiver.played if waiver else None
        else:
            played = None
        if player is not None:
            org = await get_by_player_or_none(player=player, game=game, dao=self.org_dao)
        else:
            org = None
        return MyRole(
            team=team,
            waiver_vote=played,
            org=org,
        )


@dataclass(kw_only=True, slots=True, frozen=True)
class GamePlayReaderInteractor:
    current_game: CurrentGameProvider
    game_play_dao: GamePlayDao

    async def __call__(self, identity: IdentityProvider) -> CurrentHintsAndKeys:
        hints_ = await self.game_play_dao.get_current_hints(identity)
        events = await self.game_play_dao.get_events(identity)
        keys = await self.game_play_dao.get_team_typed_keys(identity)
        game = await self.current_game.get_required_full_game()
        level_numbers_by_name_id = {level.name_id: level.number_in_game for level in game.levels}
        return CurrentHintsAndKeys(
            hints=hints_.hints,
            typed_keys=keys,
            level_number=hints_.level_number,
            started_at=hints_.started_at,
            game_id=hints_.game_id,
            level_time_id=hints_.level_time_id,
            events=events,
            is_finished=hints_.is_finished,
            level_numbers_by_name_id=level_numbers_by_name_id,
        )


@dataclass(kw_only=True, slots=True, frozen=True)
class PassedLevelsReaderInteractor:
    """Hints of the levels the team has already passed.

    Kept apart from :class:`GamePlayReaderInteractor` on purpose: the current
    level is polled every few seconds, while the passed ones only grow when a
    level is left, so the client asks for them separately and only on demand.
    """

    game_play_dao: GamePlayDao

    async def __call__(self, identity: IdentityProvider) -> PassedLevels:
        return await self.game_play_dao.get_passed_levels(identity)


@dataclass(kw_only=True)
class GamePlayBaseInteractor:
    """
    :param dao: Слой доступа к бд.
    :param sender: Отправляет то, что надо показать, во вьюхи (после коммита).
    :param locker: Локи для обеспечения последовательного исполнения определённых операций.
    :param scheduler: Планировщик подсказок.
    """

    dao: GamePlayerDao
    sender: ViewSender
    locker: KeyCheckerFactory
    scheduler: Scheduler
    current_game: CurrentGameProvider

    async def all_teams_finished(self, game: dto.FullGame) -> ShowTasks:
        tasks = ShowTasks()
        await self.dao.finish(game)
        tasks.log.append(GameLogEvent(GameLogType.GAME_FINISHED, {"game": game.name}))
        self.locker.clear()
        for team in await self.dao.get_played_teams(game):
            tasks.view.append(GameFinishedByAll(team=team))
        return tasks

    async def process_level_up(
        self,
        input_container: InputContainer,
        team: dto.Team,
        game: dto.FullGame,
        at: datetime,
    ) -> ShowTasks:
        tasks = ShowTasks()
        async with self.locker.lock_globally():
            if await self.dao.is_team_finished(team, game):
                tasks.view.append(GameFinished(team=team, input_container=input_container))
                if await self.dao.is_all_team_finished(game):
                    tasks.extend(await self.all_teams_finished(game))
                return tasks
        return await self.process_plain_level_up(team, game, at)

    async def process_plain_level_up(
        self,
        team: dto.Team,
        game: dto.FullGame,
        now: datetime,
    ) -> ShowTasks:
        tasks = ShowTasks()
        next_level = await self.dao.get_current_level(team, game)
        lt = await self.dao.get_current_level_time(team, game)

        tasks.view.append(SendPuzzle(team=team, level=next_level))
        await schedule_first_hint(
            scheduler=self.scheduler,
            team=team,
            next_level=next_level,
            lt_id=lt.id,
            now=now,
        )
        level_up_event = LevelUp(
            team=team, new_level=next_level, orgs_list=await get_spying_orgs(game, self.dao)
        )
        tasks.org.append(level_up_event)
        return tasks


@dataclass(kw_only=True)
class CheckKeyInteractor(GamePlayBaseInteractor):
    key_processor: KeyProcessor

    async def __call__(
        self,
        key: str,
        input_container: InputContainer,
        identity: IdentityProvider,
    ) -> list[AnyViewTask]:
        """
        Проверяет введённый игроком ключ. Может случиться несколько исходов:
        - ключ неверный - просто записываем его в лог и уведомляем команду
        - ключ верный, но уже был введён ранее - записываем в лог и уведомляем команду
        - ключ верный, но ещё не все ключи найдены - записываем в лог, уведомляем команду
        - ключ верный и больше на уровне не осталось ненайденных ключей:
          * уровень не последний - переводим команду на следующий уровень, уведомляем оргов,
            присылаем команде новую загадку, планируем отправку подсказки
          * уровень последний - поздравляем команду с завершением игры
          * уровень последний и все команды финишировали - помечаем игру законченной,
            пишем в лог игры уведомление о финале, уведомляем команды

        :param key: Введённый ключ.
        :param identity: Идентичность игрока, который ввёл ключ
        :param input_container: штуковина связанная со вьюхой
        """
        now = datetime.now(tz=tz_utc)
        game = await self.current_game.get_required_full_game()
        player = await identity.get_required_player()
        team = await identity.get_required_team()
        if not await self.current_game.is_player_played(identity):
            raise exceptions.WaiverError(
                team=team, game=game, player=player, text="игрок не заявлен на игру, но ввёл ключ"
            )

        new_key = await self.key_processor.check_key(key=key, player=player, team=team, now=now)
        if new_key is None:
            return []
        tasks = ShowTasks(view=self.view_(new_key, input_container))
        if not new_key.is_duplicate and new_key.is_level_up():
            tasks.extend(
                await self.process_level_up(
                    input_container=input_container,
                    team=team,
                    game=game,
                    at=now,
                )
            )
        # nothing is shown until this lands: until now the tasks are only a list
        await self.dao.commit()
        await self.sender.show_later(tasks)
        return tasks.view

    @staticmethod
    def view_(new_key: dto.InsertedKey, input_container: InputContainer) -> list[AnyViewTask]:
        if new_key.is_duplicate:
            # if duplicate - only show info about doubles, do not repeat bonuses or other effects
            return [DuplicateKey(key=new_key, input_container=input_container)]
        match new_key.type_:
            case enums.KeyType.wrong:
                return [WrongKey(key=new_key, input_container=input_container)]
            case enums.KeyType.effects | enums.KeyType.bonus | enums.KeyType.simple:
                return [
                    EffectsKey(
                        key=new_key,
                        effects=new_key.parsed_key.effect,
                        input_container=input_container,
                    )
                ]
            case _:
                typing.assert_never(new_key.type_)


@dataclass(kw_only=True)
class GamePlayTimerInteractor(GamePlayBaseInteractor):
    processor: TimerProcessor

    async def __call__(
        self,
        team_id: int,
        now: datetime,
        started_level_time_id: int,
        input_container: SchedulerContainer,
    ) -> None:
        team = await self.dao.get_by_id(team_id)
        game = await self.current_game.get_required_full_game()
        level_time = await self.dao.get_current_level_time(team, game)
        effects_list = await self.processor.process(
            team=team,
            now=now,
            started_level_time_id=started_level_time_id,
        )

        if not effects_list:
            logger.warning(
                "no effects after processing for team %s on lt %s", team_id, started_level_time_id
            )
            return

        tasks = ShowTasks()
        level_up_effect: action.Effects | None = None
        last_event: dto.GameEvent | None = None
        for effects in effects_list:
            last_event = await self.dao.save_event(
                team=team,
                game=game,
                level_time=level_time,
                effects=effects,
            )
            tasks.view.append(
                ShowEffects(team=team, effects=effects, input_container=input_container)
            )
            if effects.level_up:
                level_up_effect = effects
        if last_event is not None:
            await self.dao.save_timer(level_time, last_event)
        if level_up_effect is not None:
            tasks.extend(
                await self.process_level_up(
                    input_container=input_container,
                    team=team,
                    game=game,
                    at=now,
                )
            )
        await self.dao.commit()
        await self.sender.show_later(tasks)
