import logging
from io import BytesIO
from pathlib import PurePosixPath
from typing import Annotated
from urllib.parse import quote

from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Body, File, Query, UploadFile
from fastapi.params import Path
from fastapi.responses import Response

from shvatka.api.dependencies.auth import ApiIdentityProvider
from shvatka.api.models import responses, req
from shvatka.api.utils.error_converter import to_http_error
from shvatka.core.games.interactors import (
    GameFileReaderInteractor,
)
from shvatka.core.games.editor_interactors import (
    RenameGameFileInteractor,
    UploadGameFileInteractor,
)
from shvatka.core.interfaces.clients.file_storage import FileStorage
from shvatka.core.models.dto import hints
from shvatka.core.utils.exceptions import UnsupportedFileFormat


logger = logging.getLogger(__name__)


@inject
async def get_game_file(
    identity: FromDishka[ApiIdentityProvider],
    file_reader: FromDishka[GameFileReaderInteractor],
    storage: FromDishka[FileStorage],
    id_: Annotated[int, Path(alias="id")],
    guid: Annotated[str, Path(alias="guid")],
) -> Response:
    meta = await file_reader(guid=guid, identity=identity, game_id=id_)
    if not await storage.exists(meta.file_content_link):
        logger.warning(
            "file %s of game %s is registered but missing on disk at %s",
            guid,
            id_,
            meta.file_content_link.file_path,
        )
        # the file is gone; answer with a non-cacheable 404 so a later upload is
        # picked up instead of a stale 404 being served from the browser cache.
        return Response(status_code=404, headers={"Cache-Control": "no-store"})
    # serve by the stored physical path, not by guid: the two can differ (e.g. for
    # files saved under a shared physical name), and only file_path is authoritative.
    local_file_name = PurePosixPath(meta.file_content_link.file_path).name
    if meta.public_filename.isascii():
        fallback = meta.public_filename
    else:
        fallback = "document" + (meta.extension or "")
    encoded = quote(meta.public_filename, safe="")
    content_disposition = f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{encoded}"
    return Response(
        headers={
            "X-Accel-Redirect": f"/protected-files/{local_file_name}",
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
    allow_conversion: Annotated[bool, Query()] = True,
    save_unsupported_as_is: Annotated[bool, Query()] = False,
) -> responses.UploadedFile:
    options = hints.FileUploadOptions(
        allow_conversion=allow_conversion,
        save_unsupported_as_is=save_unsupported_as_is,
    )
    content = BytesIO(await file.read())
    try:
        saved = await interactor(
            game_id=id_,
            content=content,
            original_filename=file.filename or "document",
            identity=identity,
            options=options,
        )
    except UnsupportedFileFormat as e:
        raise to_http_error(e, code=415) from e
    return responses.UploadedFile.from_core(saved)


@inject
async def rename_game_file(
    identity: FromDishka[ApiIdentityProvider],
    interactor: FromDishka[RenameGameFileInteractor],
    id_: Annotated[int, Path(alias="id")],
    guid: Annotated[str, Path(alias="guid")],
    body: Annotated[req.RenameFile, Body()],
) -> responses.GameFile:
    renamed = await interactor(
        game_id=id_,
        guid=guid,
        filename=body.filename,
        identity=identity,
    )
    return responses.GameFile.from_core(renamed)


def setup() -> APIRouter:
    router = APIRouter(prefix="/cdn")
    router.add_api_route("/games/{id}/files", upload_game_file, methods=["POST"])
    router.add_api_route("/games/{id}/files/{guid}", get_game_file, methods=["GET"])
    router.add_api_route("/games/{id}/files/{guid}", rename_game_file, methods=["PATCH"])
    return router
