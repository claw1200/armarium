from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.api.context import app_context
from app.catalog.paths import audio_disk_path, media_type_for, parse_file_path

router = APIRouter()


@router.api_route("/audio/{path:path}", methods=["GET", "HEAD"])
def stream_audio(request: Request, path: str) -> FileResponse:
    try:
        relative = parse_file_path(path)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    ctx = app_context(request)
    record = ctx.store.get(relative)
    if record is None:
        raise HTTPException(status_code=404, detail="not found")
    disk_path = audio_disk_path(ctx.settings.library_root, record.relative_path)
    if disk_path is None:
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(
        disk_path,
        media_type=media_type_for(record.format),
        filename=record.name,
        content_disposition_type="inline",
    )
