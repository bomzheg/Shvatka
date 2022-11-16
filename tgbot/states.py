from aiogram.fsm.state import StatesGroup, State


class MyGamesPanel(StatesGroup):
    choose_game = State()
    game_menu = State()
    rename = State()


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


class LevelManageSG(StatesGroup):
    menu = State()


class GameWriteSG(StatesGroup):
    game_name = State()
    levels = State()


class GameEditSG(StatesGroup):
    current_levels = State()
    add_level = State()


class GameOrgs(StatesGroup):
    orgs_list = State()
    org_menu = State()


class MainMenu(StatesGroup):
    main = State()


class Promotion(StatesGroup):
    disclaimer = State()


class LevelTest(StatesGroup):
    wait_key = State()


class OrgSpy(StatesGroup):
    main = State()
    spy = State()
    keys = State()
