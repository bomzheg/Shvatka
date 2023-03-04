from aiogram.utils.markdown import html_decoration as hd

from src.core.models import dto


def get_small_card_no_link(player: dto.Player) -> str:
    if player.get_tg_username():
        rez = hd.link(hd.quote(player.name_mention), f"t.me/{player.get_tg_username()}")
    else:
        rez = hd.quote(player.name_mention)
    return rez


def get_small_card(player: dto.Player, notification: bool) -> str:
    if notification:
        return render_small_card_link(player)
    return get_small_card_no_link(player)


def render_small_card_link(player: dto.Player) -> str:
    return hd.link(player.name_mention, f"tg://user?id={player.get_chat_id()}")
