from aiogram import Dispatcher

from .manage import setup_team_manage


def setup(dp: Dispatcher):
    setup_team_manage(dp)
