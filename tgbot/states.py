from aiogram.fsm.state import StatesGroup, State


class MyGamesPanel(StatesGroup):
    choose_game = State()
    game_menu = State()
    game_schedule_date = State()
    game_schedule_time = State()
    game_schedule_confirm = State()


class TimeHint(StatesGroup):
    time = State()
    hint = State()
