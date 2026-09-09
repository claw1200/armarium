from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from app.api.context import app_context
from app.catalog.models import FileRecord, FolderEntry
from app.catalog.paths import parse_folder_path
from app.indexer.scan import scan_library

router = APIRouter()


class ScanResponse(BaseModel):
    file_count: int


class FolderResponse(BaseModel):
    name: str
    path: str


class FileResponse(BaseModel):
    name: str
    path: str
    size_bytes: int
    format: str
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None


class ListingResponse(BaseModel):
    path: str
    folders: list[FolderResponse]
    files: list[FileResponse]


@router.post("/catalog/scan", response_model=ScanResponse)
def rescan(request: Request) -> ScanResponse:
    ctx = app_context(request)
    if not ctx.settings.library_root.is_dir():
        raise HTTPException(status_code=400, detail="library root is not a directory")
    file_count = scan_library(ctx.settings.library_root, ctx.store)
    return ScanResponse(file_count=file_count)


@router.get("/catalog/entries", response_model=ListingResponse)
def list_entries(request: Request, path: str | None = Query(default=None)) -> ListingResponse:
    try:
        folder = parse_folder_path(path)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    listing = app_context(request).store.list_folder(folder)
    return ListingResponse(
        path=listing.path,
        folders=[_folder_response(entry) for entry in listing.folders],
        files=[_file_response(record) for record in listing.files],
    )


def _folder_response(entry: FolderEntry) -> FolderResponse:
    return FolderResponse(name=entry.name, path=entry.path)


def _file_response(record: FileRecord) -> FileResponse:
    return FileResponse(
        name=record.name,
        path=record.relative_path,
        size_bytes=record.size_bytes,
        format=record.format,
        duration_seconds=record.duration_seconds,
        sample_rate=record.sample_rate,
        channels=record.channels,
    )
