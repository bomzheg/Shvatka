import typing

from aiogram import Bot
from aiogram.utils.text_decorations import html_decoration as hd

from shvatka.core.models import dto
from shvatka.core.utils import exceptions


async def player_already_in_team(
    *, e: exceptions.PlayerAlreadyInTeam, bot: Bot, chat_id: int
) -> None:
    player = typing.cast(dto.Player, e.player)
    team = typing.cast(dto.Team, e.team)
    if player.get_tg_username() == "team_in_team":
        await bot.send_message(
            chat_id=chat_id,
            text=f"‼️Тим уже in_team ({hd.quote(team.name)}).\n",
        )
        return
    await bot.send_message(
        chat_id=chat_id,
        text=f"‼️Игрок {hd.quote(player.name_mention)} уже находится в команде "
        f"({hd.quote(team.name)}).\n",
    )
