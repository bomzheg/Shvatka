from typing import Iterable

from aiogram.utils.text_decorations import html_decoration as hd

from shvatka.core.models import dto
from shvatka.core.models.enums.played import Played
from shvatka.core.services.waiver import get_vote_to_voted
from shvatka.core.views.texts import WAIVER_STATUS_MEANING
from shvatka.infrastructure.db.dao.holder import HolderDao
from shvatka.tgbot import keyboards as kb
from shvatka.tgbot.views.player import get_emoji
from shvatka.tgbot.views.user import get_small_card_no_link


def render_votes(votes: dict[Played, list[dto.VotedPlayer]]) -> str:
    result = ""
    for vote, users in votes.items():
        result += WAIVER_STATUS_MEANING[vote] + f" ({len(users)}):\n"
        result += render_players(users)
        result += "\n\n"
    return result


def render_all_teams_waivers(waivers: dict[dto.Team, Iterable[dto.VotedPlayer]]) -> str:
    result = ""
    for team, user_waivers in waivers.items():
        result += hd.bold(hd.quote(team.name)) + ":\n"
        result += render_players(user_waivers)
        result += "\n\n"
    return result


def render_players(users: Iterable[dto.VotedPlayer]) -> str:
    return "\n".join(
        [get_emoji(voted.pit) + get_small_card_no_link(voted.player) for voted in users]
    )


async def get_waiver_poll_text(team: dto.Team, game: dto.Game, dao: HolderDao):
    return (
        f"Сбор вейверов на игру:\n"
        f"{hd.bold(hd.quote(game.name))}\n\n{await get_list_pool(team, dao)}"
    )


async def get_waiver_final_text(team: dto.Team, game: dto.Game, dao: HolderDao):
    return (
        f"Сбор вейверов на игру {hd.bold(hd.quote(game.name))} окончен. \n"
        f"Итоговый список:\n\n"
        f"{await get_list_pool(team, dao)}"
    )


async def get_list_pool(team: dto.Team, dao: HolderDao) -> str:
    votes = await get_vote_to_voted(team, dao.waiver_vote_getter)
    return render_votes(votes)


async def start_approve_waivers(game: dto.Game, team: dto.Team, dao: HolderDao):
    votes = await get_vote_to_voted(team=team, dao=dao.waiver_vote_getter)
    return dict(
        text=f"Играющие в {hd.quote(game.name)} схватчики команды {hd.bold(hd.quote(team.name))}:",
        reply_markup=kb.get_kb_manage_waivers(
            team, map(lambda v: v.player, votes.get(Played.yes, [])), game
        ),
        disable_web_page_preview=True,
    )
