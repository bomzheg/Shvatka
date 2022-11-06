from aiogram_dialog import DialogManager


def get_game_name(dialog_manager: DialogManager, **_):
    data = dialog_manager.dialog_data
    return {
        "game_name": data["game_name"]
    }
