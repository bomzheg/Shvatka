from aiogram.dispatcher.fsm.state import StatesGroup, State


class MyGamesPanel(StatesGroup):
    choose_game = State()
    game_menu = State()
