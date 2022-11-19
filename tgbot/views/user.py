from aiogram.utils.markdown import html_decoration as hd

from shvatka.models import dto


def get_small_card_no_link(user: dto.User) -> str:
    if user.username:
        rez = hd.link(hd.quote(user.fullname), f"t.me/{user.username}")
    else:
        rez = hd.quote(user.fullname)
    return rez


def get_small_card(user: dto.User, notification: bool) -> str:
    if notification:
        return render_small_card_link(user)
    return get_small_card_no_link(user)


def render_small_card_link(user: dto.User) -> str:
    return hd.link(user.name_mention, f"tg://user?id={user.tg_id}")
