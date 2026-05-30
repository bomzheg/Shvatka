import logging
from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi.params import Path
from fastapi.responses import Response

from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.core.games.interactors import (
    GameFileReaderInteractor,
)


logger = logging.getLogger(__name__)


@inject
async def get_game_file(
    identity: FromDishka[ApiIdentityProvider],
    file_reader: FromDishka[GameFileReaderInteractor],
    id_: Annotated[int, Path(alias="id")],
    guid: Annotated[str, Path(alias="guid")],
) -> Response:
    meta = await file_reader(guid=guid, identity=identity, game_id=id_)
    return Response(
        headers={
            "X-Accel-Redirect": f"/protected-files/{meta.local_file_name}",
            "Content-Disposition": f'attachment; filename="{meta.original_filename}"',
            "Cache-Control": "private, max-age=86400",
            "Vary": "Authorization, Cookie",
        }
    )


def setup() -> APIRouter:
    router = APIRouter(prefix="/sdn")
    router.add_api_route("/games/{id}/files/{guid}", get_game_file, methods=["GET"])
    return router
