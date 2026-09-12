import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audio import router as audio_router
from app.api.catalog import router as catalog_router
from app.api.context import AppContext
from app.catalog.store import CatalogStore
from app.config import Settings
from app.indexer.runner import LibraryScanner


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        store = CatalogStore(resolved.database_path)
        store.initialize()
        scanner = LibraryScanner(resolved, store)
        scanner.bind(asyncio.get_running_loop())
        application.state.ctx = AppContext(settings=resolved, store=store, scanner=scanner)
        await scanner.start()
        try:
            yield
        finally:
            await scanner.wait()
            store.close()

    application = FastAPI(title="Armarium", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
        allow_headers=["*"],
    )
    application.include_router(catalog_router)
    application.include_router(audio_router)
    return application


app = create_app()
