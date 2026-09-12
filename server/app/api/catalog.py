import asyncio
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request, WebSocket
from pydantic import BaseModel
from starlette.websockets import WebSocketDisconnect

from app.api.context import app_context
from app.catalog.models import FileMeta, FileRecord, FolderEntry
from app.catalog.paths import parse_folder_path
from app.catalog.store import FILE_SORTS, CatalogStore

MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 50
MAX_QUERY_LENGTH = 200

router = APIRouter()


class ScanResponse(BaseModel):
    status: Literal["started", "running"]


class FolderResponse(BaseModel):
    name: str
    path: str


class FileResponse(BaseModel):
    name: str
    path: str
    parent_path: str
    size_bytes: int
    format: str
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None
    bpm: float | None
    key: str | None
    tags: list[str]


class ListingResponse(BaseModel):
    path: str
    folders: list[FolderResponse]
    files: list[FileResponse]


class FilesResponse(BaseModel):
    items: list[FileResponse]
    total: int
    limit: int
    offset: int


@router.post("/catalog/scan", response_model=ScanResponse)
async def rescan(request: Request) -> ScanResponse:
    ctx = app_context(request)
    if not ctx.settings.library_root.is_dir():
        raise HTTPException(status_code=400, detail="library root is not a directory")
    started = await ctx.scanner.start()
    return ScanResponse(status="started" if started else "running")


@router.websocket("/catalog/scan")
async def scan_progress(websocket: WebSocket) -> None:
    await websocket.accept()
    ctx = app_context(websocket)
    queue = ctx.scanner.subscribe()
    try:
        await websocket.send_json(ctx.scanner.snapshot().as_dict())
        while True:
            progress = asyncio.create_task(queue.get())
            incoming = asyncio.create_task(websocket.receive())
            done, pending = await asyncio.wait(
                {progress, incoming}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            for task in pending:
                try:
                    await task
                except (asyncio.CancelledError, WebSocketDisconnect):
                    pass
            if progress in done:
                await websocket.send_json(progress.result().as_dict())
            if incoming in done:
                error = incoming.exception()
                if error is not None and not isinstance(error, WebSocketDisconnect):
                    raise error
                return
    except WebSocketDisconnect:
        return
    finally:
        ctx.scanner.unsubscribe(queue)


@router.get("/catalog/entries", response_model=ListingResponse)
def list_entries(request: Request, path: str | None = Query(default=None)) -> ListingResponse:
    try:
        folder = parse_folder_path(path)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    ctx = app_context(request)
    listing = ctx.store.list_folder(folder)
    return ListingResponse(
        path=listing.path,
        folders=[_folder_response(entry) for entry in listing.folders],
        files=_file_responses(ctx.store, listing.files),
    )


@router.get("/catalog/files", response_model=FilesResponse)
def list_files(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    request: Request,
    limit: int = Query(default=DEFAULT_PAGE_SIZE),
    offset: int = Query(default=0),
    prefix: str | None = Query(default=None),
    q: str | None = Query(default=None),
    sort: str = Query(default="path"),
    tag: list[str] | None = Query(default=None),
) -> FilesResponse:
    if not 1 <= limit <= MAX_PAGE_SIZE:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")
    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be >= 0")
    if sort not in FILE_SORTS:
        raise HTTPException(status_code=400, detail="invalid sort")
    query = (q or "").strip()
    if len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(status_code=400, detail="q must be at most 200 characters")
    try:
        folder = parse_folder_path(prefix)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    ctx = app_context(request)
    try:
        page = ctx.store.list_files(
            offset=offset, limit=limit, prefix=folder, query=query, sort=sort, tags=tag or []
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return FilesResponse(
        items=_file_responses(ctx.store, page.items),
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


def _folder_response(entry: FolderEntry) -> FolderResponse:
    return FolderResponse(name=entry.name, path=entry.path)


def _file_responses(store: CatalogStore, records: list[FileRecord]) -> list[FileResponse]:
    paths = [record.relative_path for record in records]
    meta = store.meta_by_paths(paths)
    tags = store.tags_by_paths(paths)
    return [
        _file_response(record, meta.get(record.relative_path), tags.get(record.relative_path, []))
        for record in records
    ]


def _file_response(
    record: FileRecord, meta: FileMeta | None, tags: list[str]
) -> FileResponse:
    return FileResponse(
        name=record.name,
        path=record.relative_path,
        parent_path=record.parent_path,
        size_bytes=record.size_bytes,
        format=record.format,
        duration_seconds=record.duration_seconds,
        sample_rate=record.sample_rate,
        channels=record.channels,
        bpm=meta.bpm if meta is not None else None,
        key=meta.key if meta is not None else None,
        tags=tags,
    )
