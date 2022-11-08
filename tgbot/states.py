from aiogram.fsm.state import StatesGroup, State


class MyGamesPanel(StatesGroup):
    choose_game = State()
    game_menu = State()


class GameSchedule(StatesGroup):
    date = State()
    time = State()
    confirm = State()


class TimeHintSG(StatesGroup):
    time = State()
    hint = State()


class LevelSG(StatesGroup):
    level_id = State()
    keys = State()
    time_hints = State()


class GameWriteSG(StatesGroup):
    game_name = State()
    levels = State()


class GameEditSG(StatesGroup):
    current_levels = State()
