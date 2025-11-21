import logging
from dataclasses import dataclass
from datetime import datetime

from shvatka.core.interfaces.current_game import CurrentGameProvider
from shvatka.core.interfaces.dal.game_play import GamePlayerDao
from shvatka.core.models import dto, enums
from shvatka.core.models.dto import action
from shvatka.core.models.dto.action import DecisionType
from shvatka.core.utils import exceptions
from shvatka.core.utils.input_validation import is_key_valid
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory

logger = logging.getLogger(__name__)


@dataclass
class KeyProcessor:
    dao: GamePlayerDao
    current_game: CurrentGameProvider
    locker: KeyCheckerFactory

    async def check_key(
        self, key: str, team: dto.Team, player: dto.Player
    ) -> dto.InsertedKey | None:
        if not is_key_valid(key):
            raise exceptions.InvalidKey(
                key=key, team=team, player=player, game=await self.current_game.get_required_game()
            )
        return await self.submit_key(key=key, player=player, team=team)

    async def submit_key(
        self,
        key: str,
        player: dto.Player,
        team: dto.Team,
    ) -> dto.InsertedKey | None:
        game = await self.current_game.get_required_full_game()
        async with self.locker.lock_team(team):
            level_time = await self.dao.get_current_level_time(team, game)
            lvl = await self.dao.get_current_level(team, game)
            correct_keys = await self.dao.get_correct_typed_keys(
                level_time=level_time, game=game, team=team
            )
            all_typed = await self.dao.get_team_typed_keys(game, team, level_time=level_time)
            state = action.InMemoryKeyStateHolder(
                typed_correct=correct_keys,
                all_typed={k.text for k in all_typed},
            )
            decision = lvl.scenario.check(
                action_=action.TypedKeyAction(key=key),
                state=state,
            )
            if isinstance(decision, action.KeyDecision):
                saved_key = await self.dao.save_key(
                    key=decision.key_text,
                    team=team,
                    level_time=level_time,
                    game=game,
                    player=player,
                    type_=decision.key_type,
                    is_duplicate=decision.duplicate,
                )
                if is_level_up := isinstance(decision, action.LevelUpDecision):
                    await self.dao.level_up(
                        team=team,
                        level=lvl,
                        game=game,
                        next_level_number=await define_next_level(
                            dao=self.dao,
                            game=await self.current_game.get_required_full_game(),
                            level=lvl,
                            level_name=decision.next_level,
                        ),
                    )
                await self.dao.commit()
                return dto.InsertedKey.from_key_time(
                    saved_key, is_level_up, parsed_key=decision_to_parsed_key(decision)
                )
            elif isinstance(decision, action.NotImplementedActionDecision):
                logger.warning("impossible decision here cant be not implemented")
                return None
            else:
                logger.warning("impossible decision here is %s", type(decision))
                return None


async def define_next_level(
    dao: GamePlayerDao,
    game: dto.FullGame,
    level: dto.Level,
    level_name: str | None = None,
) -> int:
    if level_name is None:
        assert level.number_in_game is not None
        if len(game.levels) == level.number_in_game + 1:
            return level.number_in_game + 1
        next_level_ = await dao.get_next_level(level, game)
        assert next_level_.number_in_game is not None
        return next_level_.number_in_game
    else:
        next_level = await dao.get_level_by_name(level_name, game)
        if next_level is None:
            raise exceptions.ScenarioNotCorrect(text="Level name not found", name_id=level_name)
        assert next_level.number_in_game is not None
        return next_level.number_in_game


def decision_to_parsed_key(
    decision: action.KeyDecision,
) -> dto.ParsedKey:
    match decision:
        case action.BonusKeyDecision(key=key):
            return dto.ParsedBonusKey(
                type_=enums.KeyType.bonus,
                text=decision.key_text,
                bonus_minutes=key.bonus_minutes,
            )
        case action.WrongKeyDecision():
            return dto.ParsedKey(
                type_=decision.key_type,
                text=decision.key_text,
            )
        case action.BonusHintKeyDecision(bonus_hint=bonus_hint):
            return dto.ParsedBonusHintKey(
                type_=enums.KeyType.bonus_hint,
                text=decision.key_text,
                bonus_hint=bonus_hint,
            )
        case action.TypedKeyDecision():
            return dto.ParsedKey(
                type_=decision.key_type,
                text=decision.key_text,
            )
        case _:
            raise NotImplementedError(f"unknown decision type {type(decision)}")


@dataclass
class TimerProcessor:
    locker: KeyCheckerFactory
    dao: GamePlayerDao
    current_game: CurrentGameProvider

    async def process(
        self,
        team: dto.Team,
        now: datetime,
        started_level_time_id: int,
    ) -> action.Effects | None:
        game = await self.current_game.get_required_game()
        async with self.locker(team):
            current_level_time = await self.dao.get_current_level_time(team, game)
            lvl = await self.dao.get_current_level(team=team, game=game)
            started_level_time: dto.LevelTime = await self.dao.get_level_time_by_id(
                id_=started_level_time_id,
                team=team,
                game=game,
            )
            decision = lvl.scenario.check(
                action_=action.LevelTimerAction(now=now),
                state=action.InMemoryTimerStateHolder(
                    started_level_time_id=started_level_time_id,
                    current_level_time_id=current_level_time.id,
                    applied_effects=[
                        e.effects
                        for e in await self.dao.get_team_events(
                            team=team, level_time=started_level_time
                        )
                    ],
                    started_at=started_level_time.start_at,
                ),
            )
            if isinstance(decision, action.LevelTimerDecision):
                if isinstance(decision, action.LevelTimerEffectsDecision):
                    if decision.effects.level_up:
                        await self.dao.level_up(
                            team=team,
                            level=lvl,
                            game=game,
                            next_level_number=await define_next_level(
                                dao=self.dao,
                                game=await self.current_game.get_required_full_game(),
                                level=lvl,
                                level_name=decision.effects.next_level,
                            ),
                        )
                        await self.dao.commit()
                        return decision.effects
                    else:
                        logger.warning("unprocessable effects %s", decision.effects)
                        return None
                else:
                    logger.warning("impossible decision type here is %s %s", type(decision), decision.type)
                    return None
            elif isinstance(decision, action.NotImplementedActionDecision):
                logger.warning("impossible decision here cant be not implemented")
                return None
            else:
                logger.warning("impossible decision here is %s", type(decision))
                return None
