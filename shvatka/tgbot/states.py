from aiogram.fsm.state import StatesGroup, State


class MyGamesPanelSG(StatesGroup):
    choose_game = State()
    game_menu = State()
    rename = State()


class GameScheduleSG(StatesGroup):
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
    send_to_test = State()


class GameWriteSG(StatesGroup):
    game_name = State()
    levels = State()
    from_zip = State()


class GameEditSG(StatesGroup):
    current_levels = State()
    add_level = State()


class GameOrgsSG(StatesGroup):
    orgs_list = State()
    org_menu = State()


class MainMenuSG(StatesGroup):
    main = State()


class PromotionSG(StatesGroup):
    disclaimer = State()


class LevelTestSG(StatesGroup):
    wait_key = State()


class OrgSpySG(StatesGroup):
    main = State()
    spy = State()
    keys = State()


class GamePublishSG(StatesGroup):
    prepare = State()


class CaptainsBridgeSG(StatesGroup):
    main = State()
    name = State()
    description = State()
    players = State()
    player = State()
    confirm_delete = State()
    player_role = State()
    player_emoji = State()


class CompletedGamesPanelSG(StatesGroup):
    list = State()
    game = State()
    waivers = State()
    results = State()


class TeamsSg(StatesGroup):
    list = State()
    one = State()


class PlayerSg(StatesGroup):
    main = State()
