from aiogram_dialog import DialogManager


async def get_game_id(dialog_manager: DialogManager, **_):
    data = dialog_manager.dialog_data
    return {
        "game_id": data["game_id"]
    }


async def get_orgs(dialog_manager: DialogManager, **_):

    return {

    }
