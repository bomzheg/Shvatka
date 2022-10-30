from aiogram.utils.text_decorations import html_decoration as hd

from db.dao.holder import HolderDao
from shvatka.models import dto
from shvatka.models.enums.played import Played
from shvatka.services.waiver import get_vote_to_voted
from shvatka.views.texts import WAIVER_STATUS_MEANING
from tgbot.views.player import get_emoji
from tgbot.views.user import get_small_card_no_link


def render_votes(votes: dict[Played, list[dto.VotedPlayer]]) -> str:
    result = ""
    for vote, users in votes.items():
        users: list[dto.VotedPlayer]
        result += WAIVER_STATUS_MEANING[vote] + f" ({len(users)}):\n"
        result += "\n".join([get_emoji(voted.pit) + get_small_card_no_link(voted.player.user) for voted in users])
        result += "\n\n"
    return result


async def get_waiver_poll_text(team: dto.Team, game: dto.Game, dao: HolderDao):
    return f"Сбор вейверов на игру:\n{hd.bold(game.name)}\n\n{await get_list_pool(team, dao)}"


async def get_list_pool(team: dto.Team, dao: HolderDao) -> str:
    votes = await get_vote_to_voted(team, dao.waiver_vote_getter)
    return render_votes(votes)
