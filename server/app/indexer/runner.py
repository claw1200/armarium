from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from threading import Lock
from typing import Literal

from app.catalog.store import CatalogStore
from app.config import Settings
from app.indexer.form import estimator_for
from app.indexer.scan import scan_library

logger = logging.getLogger(__name__)

ScanStatus = Literal["idle", "running"]
_PROGRESS_INTERVAL_S = 0.05


@dataclass(frozen=True, slots=True)
class ScanProgress:
    status: ScanStatus
    done: int
    total: int

    def as_dict(self) -> dict[str, str | int]:
        return {"status": self.status, "done": self.done, "total": self.total}


class ScanHub:
    def __init__(self) -> None:
        self._lock = Lock()
        self._progress = ScanProgress("idle", 0, 0)
        self._subscribers: set[asyncio.Queue[ScanProgress]] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._last_emit = 0.0

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def snapshot(self) -> ScanProgress:
        with self._lock:
            return self._progress

    def subscribe(self) -> asyncio.Queue[ScanProgress]:
        queue: asyncio.Queue[ScanProgress] = asyncio.Queue(maxsize=1)
        with self._lock:
            self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[ScanProgress]) -> None:
        with self._lock:
            self._subscribers.discard(queue)

    def begin(self) -> None:
        self.publish(ScanProgress("running", 0, 0))

    def report(self, done: int, total: int) -> None:
        self.publish(ScanProgress("running", done, total))

    def finish(self) -> None:
        with self._lock:
            current = self._progress
        self.publish(ScanProgress("idle", current.done, current.total))

    def publish(self, progress: ScanProgress) -> None:
        with self._lock:
            previous = self._progress
            self._progress = progress
            if not _should_emit(previous, progress, self._last_emit):
                return
            self._last_emit = time.monotonic()
            subscribers = list(self._subscribers)
            loop = self._loop
        if loop is None:
            return
        for queue in subscribers:
            loop.call_soon_threadsafe(_push, queue, progress)


class LibraryScanner:
    def __init__(self, settings: Settings, store: CatalogStore) -> None:
        self._settings = settings
        self._store = store
        self._hub = ScanHub()
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        self._hub.bind(loop)

    def snapshot(self) -> ScanProgress:
        return self._hub.snapshot()

    def subscribe(self) -> asyncio.Queue[ScanProgress]:
        return self._hub.subscribe()

    def unsubscribe(self, queue: asyncio.Queue[ScanProgress]) -> None:
        self._hub.unsubscribe(queue)

    async def start(self) -> bool:
        async with self._lock:
            if self._task is not None and not self._task.done():
                return False
            self._hub.begin()
            self._task = asyncio.create_task(self._run())
            self._task.add_done_callback(_log_scan_task)
            return True

    async def wait(self) -> None:
        task = self._task
        if task is not None:
            await asyncio.gather(task, return_exceptions=True)

    async def _run(self) -> None:
        try:
            if self._settings.library_root.is_dir():
                await asyncio.to_thread(self._scan)
        finally:
            self._hub.finish()

    def _scan(self) -> int:
        return scan_library(
            self._settings.library_root,
            self._store,
            form_estimator=estimator_for(self._settings.loop_tempo_estimator),
            on_progress=self._hub.report,
        )


def _log_scan_task(task: asyncio.Task[None]) -> None:
    if task.cancelled():
        return
    error = task.exception()
    if error is not None:
        logger.error("catalog scan failed", exc_info=error)


def _should_emit(previous: ScanProgress, progress: ScanProgress, last_emit: float) -> bool:
    if progress.status != previous.status:
        return True
    if progress.status == "idle" or progress.done == 0:
        return True
    if progress.total > 0 and progress.done >= progress.total:
        return True
    return time.monotonic() - last_emit >= _PROGRESS_INTERVAL_S


def _push(queue: asyncio.Queue[ScanProgress], progress: ScanProgress) -> None:
    if queue.full():
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
    try:
        queue.put_nowait(progress)
    except asyncio.QueueFull:
        pass
