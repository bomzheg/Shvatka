from aiogram import Dispatcher

from .manage import setup_team_manage


def setup_team_handlers(dp: Dispatcher):
    setup_team_manage(dp)
