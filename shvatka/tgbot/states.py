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


class TimeHintEditSG(StatesGroup):
    details = State()
    time = State()


class LevelListSG(StatesGroup):
    levels = State()


class LevelSG(StatesGroup):
    level_id = State()
    menu = State()


class LevelEditSg(StatesGroup):
    menu = State()


class LevelKeysSG(StatesGroup):
    keys = State()


class LevelBonusKeysSG(StatesGroup):
    bonus_keys = State()


class LevelHintsSG(StatesGroup):
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
    forum = State()


class CaptainsBridgeSG(StatesGroup):
    main = State()
    name = State()
    description = State()
    players = State()
    add_player = State()
    player = State()
    confirm_delete = State()
    player_role = State()
    player_emoji = State()


class MergePlayersSG(StatesGroup):
    main = State()
    input = State()
    confirm = State()


class MergeTeamsSG(StatesGroup):
    main = State()
    list_forum = State()
    confirm = State()


class CompletedGamesPanelSG(StatesGroup):
    list = State()
    game = State()
    waivers = State()
    results = State()
    scenario_channel = State()
    keys = State()


class TeamsSg(StatesGroup):
    filter = State()
    list = State()
    one = State()


class MyTeamSg(StatesGroup):
    team = State()


class PlayerSg(StatesGroup):
    main = State()
