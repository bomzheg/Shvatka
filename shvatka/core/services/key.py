import logging
from dataclasses import dataclass


from shvatka.core.interfaces.dal.game_play import GamePlayerDao
from shvatka.core.models import dto
from shvatka.core.models.dto.scn import action
from shvatka.core.utils import exceptions
from shvatka.core.utils.input_validation import is_key_valid
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory


logger = logging.getLogger(__name__)


@dataclass
class KeyProcessor:
    dao: GamePlayerDao
    game: dto.FullGame
    locker: KeyCheckerFactory

    async def check_key(self, key: str, team: dto.Team, player: dto.Player) -> dto.InsertedKey:
        if not is_key_valid(key):
            raise exceptions.InvalidKey(key=key, team=team, player=player, game=self.game)
        return await self.submit_key(key=key, player=player, team=team)

    async def submit_key(
        self,
        key: str,
        player: dto.Player,
        team: dto.Team,
    ) -> dto.InsertedKey:
        async with self.locker(team):
            level = await self.dao.get_current_level(team, self.game)
            correct_keys = await self.dao.get_correct_typed_keys(
                level=level, game=self.game, team=team
            )
            all_typed = await self.dao.get_team_typed_keys(
                self.game, team, level_number=level.number_in_game
            )
            state = action.InMemoryStateHolder(
                typed_correct=correct_keys,
                all_typed={k.text for k in all_typed},
            )
            decision = level.scenario.check(
                action=action.TypedKeyAction(key=key),
                state=state,
            )
            if isinstance(decision, action.KeyDecision | action.BonusKeyDecision):
                saved_key = await self.dao.save_key(
                    key=decision.key_text,
                    team=team,
                    level=level,
                    game=self.game,
                    player=player,
                    type_=decision.key_type,
                    is_duplicate=decision.duplicate,
                )
                if is_level_up := decision.type == action.DecisionType.LEVEL_UP:
                    await self.dao.level_up(team=team, level=level, game=self.game)
                await self.dao.commit()
                return dto.InsertedKey.from_key_time(
                    saved_key, is_level_up, parsed_key=decision.to_parsed_key()
                )
