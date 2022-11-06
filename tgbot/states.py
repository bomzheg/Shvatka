from aiogram.fsm.state import StatesGroup, State


class MyGamesPanel(StatesGroup):
    choose_game = State()
    game_menu = State()
    game_schedule_date = State()
    game_schedule_time = State()
    game_schedule_confirm = State()


class TimeHintSG(StatesGroup):
    time = State()
    hint = State()


class LevelSG(StatesGroup):
    level_id = State()
    keys = State()
    time_hints = State()


class GameSG(StatesGroup):
    game_name = State()
    levels = State()
