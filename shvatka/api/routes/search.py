from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi.params import Query

from shvatka.api.models import responses
from shvatka.core.search.dto import SearchFilters
from shvatka.core.search.interactors import GlobalSearchInteractor


@inject
async def global_search(
    interactor: FromDishka[GlobalSearchInteractor],
    query: Annotated[str, Query(min_length=1)],
    games: Annotated[bool, Query()] = True,
    levels: Annotated[bool, Query()] = True,
    teams: Annotated[bool, Query()] = True,
    players: Annotated[bool, Query()] = True,
) -> responses.Page[responses.SearchResult]:
    results = await interactor(
        query=query,
        filters=SearchFilters(games=games, levels=levels, teams=teams, players=players),
    )
    return responses.search_results_to_page(results)


def setup() -> APIRouter:
    router = APIRouter(prefix="/search", tags=["search"])
    router.add_api_route("", global_search, methods=["GET"])
    return router
