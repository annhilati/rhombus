from __future__ import annotations

from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
import threading, time

from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver
from watchdog.events import FileSystemEventHandler
import fastapi, uvicorn

from rhombus import Density
from rhombus.core import BeetFile


service = fastapi.FastAPI()

@dataclass
class AppContext:
    watch_path: str
    density_items: list[tuple[str, Density]]

    latest_results: list[dict[str, Any]] = field(default_factory=list)
    latest_data:    dict[str, BeetFile]  = field(default_factory=dict)

    last_change: dict | None = None
    last_error: str | None = None

    rebuild_event:  threading.Event = field(default_factory=threading.Event)
    shutdown_event: threading.Event = field(default_factory=threading.Event)
    compile_lock:   threading.Lock  = field(default_factory=threading.Lock)

    observer: BaseObserver | None = None

ctx: AppContext | None = None

class Handler(FileSystemEventHandler):
    def on_any_event(self, event):
        # Optional: wenn du Ordner-Events ignorieren willst, hier aktivieren:
        # if event.is_directory:
        #     return

        ctx.last_change = {
            "type": event.event_type,
            "path": event.src_path,
            "time": time.time(),
        }
        ctx.rebuild_event.set()


def rebuild_all() -> dict[str, Any]:
    """
    Ruft bei jeder Density compile(string) auf.
    Die Ergebnisse werden in Reihenfolge gemerged.
    Spätere Dicts überschreiben frühere.
    """
    merged: dict[str, BeetFile] = {}
    per_density: list[dict[str, Any]] = []

    for id, (density) in ctx.density_items:
        result = density.compile(id)

        per_density.append({
            "source": id,
            "density": density.__class__.__name__,
            "result": result,
        })
        merged.update(result)

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
        "last_error": ctx.last_error,
        # "latest_results": ctx.latest_results,
        "latest_data": [
            {
                "registry": "/".join(file.__class__.scope),
                "id": id,
                "content": file.data
            }
            for id, file in ctx.latest_data.items()
        ],
    }


def start_service(path: str | Path, items: list[tuple[str, Density]]):
    global ctx
    ctx = AppContext(watch_path=str(path), density_items=items)

    uvicorn.run(service, host="127.0.0.1", port=8000)