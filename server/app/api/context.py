from dataclasses import dataclass

from fastapi import Request, WebSocket

from app.catalog.store import CatalogStore
from app.config import Settings
from app.indexer.runner import LibraryScanner


@dataclass(frozen=True, slots=True)
class AppContext:
    settings: Settings
    store: CatalogStore
    scanner: LibraryScanner


def app_context(connection: Request | WebSocket) -> AppContext:
    return connection.app.state.ctx
