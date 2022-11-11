from aiogram import Router
from aiogram.types import InlineQuery

from tgbot.keyboards.inline import AddGameOrg


async def add_org_inline_query(q: InlineQuery, inline_data: AddGameOrg):
    print(q)
    print(inline_data)


def setup() -> Router:
    router = Router(name=__name__)
    router.inline_query.register(add_org_inline_query)
    return router
