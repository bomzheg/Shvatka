from aiogram_dialog import DialogManager


def get_active_filter(dialog_manager: DialogManager):
    return dialog_manager.dialog_data.get("active", True)


def get_archive_filter(dialog_manager: DialogManager):
    return dialog_manager.dialog_data.get("archive", False)
