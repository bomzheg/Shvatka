from aiogram.dispatcher.middlewares.data import MiddlewareData
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import Context, Stack
from aiogram_dialog.context.storage import StorageProxy
from dishka import AsyncContainer


class DialogMiddlewareData(MiddlewareData, total=False):
    dialog_manager: DialogManager
    aiogd_storage_proxy: StorageProxy
    aiogd_stack: Stack
    aiogd_context: Context


class SHMiddlewareData(DialogMiddlewareData, total=False):
    dishka_container: AsyncContainer
