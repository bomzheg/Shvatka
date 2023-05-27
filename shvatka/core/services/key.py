from dataclasses import dataclass

from shvatka.core.interfaces.dal.game_play import GamePlayerDao
from shvatka.core.models import dto
from shvatka.core.models.dto import scn
from shvatka.core.utils import exceptions
from shvatka.core.utils.input_validation import is_key_valid
from shvatka.core.utils.key_checker_lock import KeyCheckerFactory


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
            new_key = await self.dao.save_key(
                key=key,
                team=team,
                level=level,
                game=self.game,
                player=player,
                is_correct=await self.is_correct(key, level),
                is_duplicate=await self.is_duplicate(level=level, team=team, key=key),
            )
            typed_keys = await self.dao.get_correct_typed_keys(
                level=level, game=self.game, team=team
            )
            if new_key.is_correct:  # add just now added key to typed, because no flush in dao
                typed_keys.add(new_key.text)
            is_level_up = await self.is_level_up(typed_keys, level)
            if is_level_up:
                await self.dao.level_up(team=team, level=level, game=self.game)
            await self.dao.commit()
        return dto.InsertedKey.from_key_time(new_key, is_level_up)

    async def is_correct(self, key: scn.SHKey, level: dto.Level) -> bool:
        return key in level.get_keys()

    async def is_duplicate(self, key: scn.SHKey, level: dto.Level, team: dto.Team) -> bool:
        return await self.dao.is_key_duplicate(level, team, key)

    async def is_level_up(self, typed_keys: set[scn.SHKey], level: dto.Level) -> bool:
        return typed_keys == level.get_keys()
