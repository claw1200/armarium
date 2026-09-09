from dataclasses import dataclass

from fastapi import Request

from app.catalog.store import CatalogStore
from app.config import Settings


@dataclass(frozen=True, slots=True)
class AppContext:
    settings: Settings
    store: CatalogStore


def app_context(request: Request) -> AppContext:
    return request.app.state.ctx
