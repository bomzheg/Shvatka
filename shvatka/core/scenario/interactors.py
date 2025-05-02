from typing import BinaryIO

from shvatka.core.interfaces.dal.game import GameByIdGetter
from shvatka.core.interfaces.printer import TablePrinter, Table, CellAddress, Cell
from shvatka.core.models import dto as core
from shvatka.core.models.dto import action
from shvatka.core.scenario import dto
from shvatka.tgbot.views.utils import render_hints

GAME_NAME = CellAddress(row=1, column=1)
FIRST_LEVEL_NUMBER = CellAddress(row=2, column=1)
FIRST_LEVEL_NAME = CellAddress(row=2, column=2)
FIRST_LEVEL_KEYS = CellAddress(row=2, column=3)
FIRST_LEVEL_KEYS_DESCRIPTION = CellAddress(row=2, column=4)

class AllGameKeysReaderInteractor:
    def __init__(self, dao: GameByIdGetter, printer: TablePrinter):
        self.dao = dao
        self.printer = printer

    async def __call__(self, game_id: int) -> BinaryIO:
        game = await self.dao.get_full(game_id)
        return self.view(game, self.presenter(game))

    def view(self, game: core.FullGame, keys: list[dto.LevelKeys]) -> BinaryIO:
        return self.printer.print_table(self.to_table(game, keys))

    def to_table(self, game: core.FullGame, keys: list[dto.LevelKeys]) -> Table:
        fields: dict[CellAddress, Cell] = {GAME_NAME: Cell(value=game.name)}
        for lk in keys:
            for key in lk.keys:
                fields[FIRST_LEVEL_NUMBER] = Cell(value=lk.level_number)
                fields[FIRST_LEVEL_NAME] = Cell(value=lk.level_name_id)
                fields[FIRST_LEVEL_KEYS] = Cell(value="\n".join(key.keys))
                fields[FIRST_LEVEL_KEYS_DESCRIPTION] = Cell(value=key.description)
        return Table(fields=fields)

    def presenter(self, game: core.FullGame) -> list[dto.LevelKeys]:
        result = []
        for level in game.levels:
            assert level.number_in_game is not None
            keys = []
            for win_condition in level.scenario.conditions.get_default_key_conditions():
                keys.extend(self.presenter_win_condition(win_condition, game.levels))
            for routed_condition in level.scenario.conditions.get_routed_conditions():
                keys.extend(self.presenter_win_condition(routed_condition, game.levels))
            for bonus_hint_condition in level.scenario.conditions.get_bonus_hints_conditions():
                keys.extend(self.presenter_bonus_hint_condition(bonus_hint_condition))
            for bonus_condition in level.scenario.conditions.get_bonus_conditions():
                keys.extend(self.presenter_bonus_condition(bonus_condition))
            lk = dto.LevelKeys(
                level_number=level.number_in_game,
                level_name_id=level.name_id,
                keys=keys,
            )
            result.append(lk)
        return result

    def presenter_win_condition(
        self, condition: action.KeyWinCondition, levels: list[core.Level]
    ) -> list[dto.Key]:
        if condition.next_level:
            next_level = next(level for level in levels if level.name_id == condition.next_level)
            return [
                dto.Key(
                    keys=condition.keys,
                    description=f"-> {next_level.name_id} ({next_level.number_in_game})",
                )
            ]
        else:
            return [
                dto.Key(
                    keys=condition.keys,
                    description="",
                )
            ]

    def presenter_bonus_hint_condition(
        self, condition: action.KeyBonusHintCondition
    ) -> list[dto.Key]:
        return [
            dto.Key(
                keys=condition.keys,
                description=f"bonus hint: {render_hints(condition.bonus_hint)}",
            )
        ]

    def presenter_bonus_condition(self, condition: action.KeyBonusCondition) -> list[dto.Key]:
        return [
            dto.Key(keys={bk.text}, description=f"{bk.bonus_minutes} мин.")
            for bk in condition.keys
        ]
