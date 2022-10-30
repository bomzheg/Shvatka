from aiogram.utils.markdown import html_decoration as hd

from shvatka.models import dto


def get_small_card_no_link(user: dto.User) -> str:
    if user.username:
        rez = hd.link(user.fullname, f"t.me/{user.username}")
    else:
        rez = hd.quote(user.fullname)
    return rez
