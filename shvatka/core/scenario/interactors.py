from typing import BinaryIO, Sequence

from shvatka.core.interfaces.dal.game import GameByIdGetter
from shvatka.core.interfaces.identity import IdentityProvider
from shvatka.core.interfaces.printer import TablePrinter, Table, CellAddress, Cell
from shvatka.core.models import dto as core
from shvatka.core.models.dto import action
from shvatka.core.rules.game import check_can_read
from shvatka.core.scenario import dto
from shvatka.core.scenario.adapters import TransitionsPrinter
from shvatka.core.views.texts import render_effects

GAME_NAME = CellAddress(row=1, column=1)
FIRST_LEVEL_NUMBER = CellAddress(row=2, column=1)
FIRST_LEVEL_NAME = CellAddress(row=2, column=2)
FIRST_LEVEL_KEYS = CellAddress(row=2, column=3)
FIRST_LEVEL_KEYS_DESCRIPTION = CellAddress(row=2, column=4)


class AllGameKeysReaderInteractor:
    def __init__(self, dao: GameByIdGetter, printer: TablePrinter):
        self.dao = dao
        self.printer = printer

    async def __call__(self, game_id: int, identity: IdentityProvider) -> BinaryIO:
        player = await identity.get_required_player()
        game = await self.dao.get_full(game_id)
        check_can_read(game, player)
        return self.view(game, self.presenter(game))

    def view(self, game: core.FullGame, keys: list[dto.LevelKeys]) -> BinaryIO:
        return self.printer.print_table(self.to_table(game, keys))

    def to_table(self, game: core.FullGame, keys: list[dto.LevelKeys]) -> Table:
        fields: dict[CellAddress, Cell] = {GAME_NAME: Cell(value=game.name)}
        i = 0
        for lk in keys:
            for key in lk.keys:
                fields[FIRST_LEVEL_NUMBER.shift(rows=i)] = Cell(value=lk.level_number)
                fields[FIRST_LEVEL_NAME.shift(rows=i)] = Cell(value=lk.level_name_id)
                fields[FIRST_LEVEL_KEYS.shift(rows=i)] = Cell(value="\n".join(key.keys))
                fields[FIRST_LEVEL_KEYS_DESCRIPTION.shift(rows=i)] = Cell(value=key.description)
                i += 1
        return Table(fields=fields)

    def presenter(self, game: core.FullGame) -> list[dto.LevelKeys]:
        result = []
        for level in game.levels:
            keys = []
            for win_condition in level.scenario.conditions.get_default_key_conditions():
                keys.extend(self.presenter_win_condition(win_condition, game.levels))
            for effects_condition in level.scenario.conditions.get_effects_key_conditions():
                keys.extend(self.presenter_effects_condition(effects_condition))
            lk = dto.LevelKeys(
                level_number=level.number_in_game,
                level_name_id=level.name_id,
                keys=keys,
            )
            result.append(lk)
        return result

    def presenter_win_condition(
        self, condition: action.KeyWinCondition, levels: Sequence[core.GamedLevel]
    ) -> list[dto.Key]:
        return [
            dto.Key(
                keys=condition.keys,
                description="",
            )
        ]

    def presenter_effects_condition(self, condition: action.KeyEffectsCondition) -> list[dto.Key]:
        return [
            dto.Key(
                keys=condition.keys,
                description=f"effects: {render_effects(condition.effects)}",
            )
        ]


class GameScenarioTransitionsInteractor:
    def __init__(self, dao: GameByIdGetter, printer: TransitionsPrinter):
        self.dao = dao
        self.printer = printer

    async def __call__(self, game_id: int, identity: IdentityProvider) -> BinaryIO:
        game = await self.dao.get_full(game_id)
        check_can_read(game, await identity.get_required_player())
        return await self.printer.render(self.printer.print(self.convert(game)))

    def convert(self, game: core.FullGame) -> dto.Transitions:
        forward_transitions: list[dto.Transition] = []
        routed_transitions: list[dto.Transition] = []
        levels_conditions: dict[str, list[tuple[str, bool]]] = {}
        prev_level: core.GamedLevel | None = None
        for level in game.levels:
            levels_conditions[level.name_id] = []
            if prev_level is not None:
                self.process_default_key_condition(
                    prev_level, level.name_id, forward_transitions, levels_conditions
                )
            routed = [
                c
                for c in level.scenario.conditions.get_effects_key_conditions()
                if c.effects.is_routed_level_up()
            ]
            for condition in routed:
                assert condition.effects.next_level is not None
                routed_transitions.append(
                    dto.Transition(
                        level.name_id,
                        condition.effects.next_level,
                        self.print_condition(condition),
                    )
                )
                levels_conditions[level.name_id].append((self.print_condition(condition), True))
            prev_level = level
        if prev_level is not None:
            self.process_default_key_condition(
                prev_level, TransitionsPrinter.FINISH_NAME, forward_transitions, levels_conditions
            )
        return dto.Transitions(
            game_name=game.name,
            levels=[dto.ShortLevel(level.number_in_game, level.name_id) for level in game.levels],
            forward_transitions=forward_transitions,
            routed_transitions=routed_transitions,
            levels_conditions=levels_conditions,
        )

    def process_default_key_condition(
        self,
        prev_level: core.GamedLevel,
        next_level_name: str,
        forward_transitions: list[dto.Transition],
        levels_conditions: dict[str, list[tuple[str, bool]]],
    ):
        for condition in prev_level.scenario.conditions.get_default_key_conditions():
            forward_transitions.append(
                dto.Transition(
                    prev_level.name_id, next_level_name, self.print_condition(condition)
                )
            )
            levels_conditions[prev_level.name_id].append((self.print_condition(condition), False))

    def print_condition(self, condition: action.KeyCondition) -> str:
        return "\\n".join(condition.get_keys())
