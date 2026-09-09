from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.catalog import AppContext, router as catalog_router
from app.catalog.store import CatalogStore
from app.config import Settings
from app.indexer.scan import scan_library


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        store = CatalogStore(resolved.database_path)
        store.initialize()
        if resolved.library_root.is_dir():
            scan_library(resolved.library_root, store)
        application.state.ctx = AppContext(settings=resolved, store=store)
        try:
            yield
        finally:
            store.close()

    application = FastAPI(title="Armarium", lifespan=lifespan)
    application.include_router(catalog_router)
    return application


app = create_app()
