import logging
from io import BytesIO
from typing import Annotated
from urllib.parse import quote

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, File, UploadFile
from fastapi.params import Path
from fastapi.responses import Response

from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.models import responses
from shvatka.core.games.interactors import (
    GameFileReaderInteractor,
)
from shvatka.core.games.editor_interactors import UploadGameFileInteractor


logger = logging.getLogger(__name__)


@inject
async def get_game_file(
    identity: FromDishka[ApiIdentityProvider],
    file_reader: FromDishka[GameFileReaderInteractor],
    id_: Annotated[int, Path(alias="id")],
    guid: Annotated[str, Path(alias="guid")],
) -> Response:
    meta = await file_reader(guid=guid, identity=identity, game_id=id_)
    if meta.public_filename.isascii():
        fallback = meta.public_filename
    else:
        fallback = "document" + (meta.extension or "")
    encoded = quote(meta.public_filename, safe="")
    content_disposition = f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{encoded}"
    logger.info("content_disposition: %s", content_disposition)
    return Response(
        headers={
            "X-Accel-Redirect": f"/protected-files/{meta.local_file_name}",
            "Content-Disposition": content_disposition,
            "Cache-Control": "private, max-age=86400",
            "Vary": "Authorization, Cookie",
        }
    )


@inject
async def upload_game_file(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[UploadGameFileInteractor],
    id_: Annotated[int, Path(alias="id")],
    file: Annotated[UploadFile, File()],
) -> responses.UploadedFile:
    content = BytesIO(await file.read())
    saved = await interactor(
        game_id=id_,
        content=content,
        original_filename=file.filename or "document",
        identity=identity,
    )
    return responses.UploadedFile.from_core(saved)


def setup() -> APIRouter:
    router = APIRouter(prefix="/cdn")
    router.add_api_route("/games/{id}/files", upload_game_file, methods=["POST"])
    router.add_api_route("/games/{id}/files/{guid}", get_game_file, methods=["GET"])
    return router
