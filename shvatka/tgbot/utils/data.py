from aiogram.dispatcher.middlewares.data import MiddlewareData
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import Stack, Context
from aiogram_dialog.context.storage import StorageProxy
from dishka import AsyncContainer


class DialogMiddlewareData(MiddlewareData, total=False):
    dialog_manager: DialogManager
    aiogd_storage_proxy: StorageProxy
    aiogd_stack: Stack
    aiogd_context: Context


class SHMiddlewareData(DialogMiddlewareData, total=False):
    """
    Data every handler receives by name.

    Nothing but the container: everything a handler needs it asks the container
    for with ``FromDishka``, including the dao and the retort. Who is acting
    comes from ``IdentityProvider`` and what is being played from
    ``CurrentGameProvider``.

    The key itself is written by dishka's aiogram integration, not by us.
    """

    dishka_container: AsyncContainer
