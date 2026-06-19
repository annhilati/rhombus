from __future__ import annotations

from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
import threading, time, sys, os

from rich import print
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver
from watchdog.events import FileSystemEventHandler
import fastapi, uvicorn
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from rhombus import Density
from rhombus.core import BeetFile, RhombusASTNode
from rhombus.core.utils import uuid_hash

service = fastapi.FastAPI()

service.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@dataclass
class AppContext:
    watch_path: str
    density_items: list[tuple[str, Density | RhombusASTNode]]

    latest_results: list[dict[str, Any]] = field(default_factory=list)
    latest_data:    dict[str, BeetFile]  = field(default_factory=dict)
    changed_files:  set[str]             = field(default_factory=set)

    last_change: float | None = None
    last_error: str | None = None

    rebuild_event:  threading.Event = field(default_factory=threading.Event)
    shutdown_event: threading.Event = field(default_factory=threading.Event)
    compile_lock:   threading.Lock  = field(default_factory=threading.Lock)

    observer: BaseObserver | None = None

ctx: AppContext | None = None

class Handler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.last_events: dict[tuple[str, str], float] = {}

    def _trigger(self, action: str, path: str):
        now = time.time()
        key = (action, path)
        if key in self.last_events and (now - self.last_events[key]) < 0.2:
            return
        self.last_events[key] = now

        print(f"[#553bd9]RHOMBUS[reset]:  {action} {path} - Building anew")
        if ctx is not None:
            ctx.changed_files.add(path)
            ctx.last_change = time.time()
            ctx.rebuild_event.set()

    def on_created(self, event):
        if not event.is_directory:
            self._trigger("Created", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._trigger("Deleted", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._trigger("Changed", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._trigger("Moved", f"{event.src_path} -> {event.dest_path}")


def rebuild_all() -> dict[str, Any]:
    """
    Ruft bei jeder Density compile(string) auf.
    Die Ergebnisse werden in Reihenfolge gemerged.
    Spätere Dicts überschreiben frühere.
    """
    merged: dict[str, Any] = {}
    per_density: list[dict[str, Any]] = []

    for (id, item) in ctx.density_items:
        if isinstance(item, Density):
            result = item.compile(id)
            per_density.append({
                "source": id,
                "density": item.__class__.__name__,
                "result": {k: getattr(v, "data", getattr(v, "text", str(v))) for k, v in result.items()},
            })
            merged.update(result)
            
        elif isinstance(item, RhombusASTNode):
            result = {}
            for node in item.inscribed_toplevel_nodes:
                result[node.reference] = node.fileclass(node.serialize_toplevel())
            result[id] = item.fileclass(item.serialize_toplevel())
            per_density.append({
                "source": id,
                "density": item.__class__.__name__,
                "result": {k: getattr(v, "data", getattr(v, "text", str(v))) for k, v in result.items()},
            })
            merged.update(result)

    ctx.last_change = time.time()
    ctx.latest_results = per_density
    ctx.latest_data = merged
    return merged


def rebuild_worker():
    """
    Wartet auf Änderungen und führt dann die Berechnung aus.
    Kleine Debounce-Phase, damit nicht jede einzelne Dateioperation sofort
    einen kompletten Rebuild auslöst.
    """
    while not ctx.shutdown_event.is_set():
        ctx.rebuild_event.wait()

        if ctx.shutdown_event.is_set():
            break

        ctx.rebuild_event.clear()

        # kurze Sammelphase für Dateispeicher-Events
        time.sleep(0.15)
        while ctx.rebuild_event.is_set():
            ctx.rebuild_event.clear()
            time.sleep(0.15)

        changed = list(ctx.changed_files)
        ctx.changed_files.clear()

        if any(f.endswith('.py') for f in changed):
            print("[#553bd9]RHOMBUS[reset]:  Restarting process to reload modules...")
            if ctx.observer is not None:
                ctx.observer.stop()
            os.execv(sys.executable, [sys.executable] + sys.argv)

        with ctx.compile_lock:
            try:
                rebuild_all()
            except Exception as exc:
                ctx.last_error = repr(exc)


def start_watcher(path: str | Path):
    observer = Observer()
    observer.schedule(Handler(), str(path), recursive=True)
    observer.start()
    ctx.observer = observer
    return observer


@service.on_event("startup")
def startup():
    start_watcher(ctx.watch_path)
    print(f"[#553bd9]RHOMBUS[reset]:  Preview service is now watching {ctx.watch_path}")

    thread = threading.Thread(target=rebuild_worker, daemon=True)
    thread.start()

    # Initiale Berechnung direkt beim Start
    with ctx.compile_lock:
        rebuild_all()


@service.on_event("shutdown")
def shutdown():
    if ctx is None:
        return

    ctx.shutdown_event.set()
    ctx.rebuild_event.set()

    if ctx.observer is not None:
        ctx.observer.stop()
        ctx.observer.join()


@service.get("/data")
def get_data():
    return {
        "last_change": ctx.last_change,
        "latest_results": ctx.latest_results,
        "latest_data": [
            {
                "registry": "/".join(getattr(file, "scope", getattr(file.__class__, "scope", ("worldgen", "density_function")))),
                "id": id,
                "content": file.data
            }
            for id, file in ctx.latest_data.items()
        ],
        "last_error": ctx.last_error,
    }

@service.get("/events")
async def get_events(request: fastapi.Request):
    async def event_generator():
        yield "retry: 500\n"
        yield "data: update\n\n"
        last_sent = ctx.last_change
        while True:
            if await request.is_disconnected():
                break
            if ctx.last_change != last_sent:
                last_sent = ctx.last_change
                yield "data: update\n\n"
            await asyncio.sleep(0.2)
    
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


def start_service(path: str | Path, *items: Density | RhombusASTNode):
    actual_items = []
    for item in items:
        if isinstance(item, list):
            actual_items.extend(item)
        else:
            actual_items.append(item)

    global ctx
    ctx = AppContext(watch_path=str(path), density_items=actual_items)

    uvicorn.run(service, host="127.0.0.1", port=8000)