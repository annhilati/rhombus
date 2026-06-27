from __future__ import annotations

from pathlib import Path
from typing import Any
from dataclasses import dataclass, field
from importlib.resources import files
import threading, time, sys, os, subprocess, traceback

from rich import print
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver
from watchdog.events import FileSystemEventHandler
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import fastapi, uvicorn, asyncio

import beet
import beet.contrib.worldgen as beet_worldgen

from rhombus import Density, t
from rhombus.core import BeetFile, RhombusASTNode, DatapackResource

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
    items: list[tuple[str, Density | RhombusASTNode | BeetFile]]

    latest_results: dict[str, BeetFile]  = field(default_factory=dict)
    changed_files:  set[str]             = field(default_factory=set)

    last_change_timestamp: float | None = None
    last_error_message: str | None = None

    rebuild_event:  threading.Event = field(default_factory=threading.Event)
    shutdown_event: threading.Event = field(default_factory=threading.Event)
    compile_lock:   threading.Lock  = field(default_factory=threading.Lock)

    observer: BaseObserver | None = None

ctx: AppContext | None = None

class Handler(FileSystemEventHandler):
    def __init__(self, watch_file: str | None = None):
        super().__init__()
        self.last_events: dict[tuple[str, str], float] = {}
        self.watch_file = watch_file

    def _trigger(self, action: str, path: str):
        if self.watch_file and Path(path).name != self.watch_file:
            return

        now = time.time()
        key = (action, path)
        if key in self.last_events and (now - self.last_events[key]) < 0.2:
            return
        self.last_events[key] = now

        try:
            rel_path = Path(path).relative_to(ctx.watch_path)
        except ValueError:
            rel_path = Path(path).name

        print(f"[#35aaf3]WATCHER[reset]:  {action} {rel_path}")
        if ctx is not None:
            ctx.changed_files.add(path)
            ctx.last_change_timestamp = time.time()
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
    files: dict[str, BeetFile] = {}
    errors: list[str] = []

    for (id, item) in ctx.items:
        try:
            if isinstance(item, Density):
                result = item.compile(id)
                files.update(result)
                
            elif isinstance(item, RhombusASTNode):
                result = {}
                for node in item.inscribed_toplevel_nodes:
                    if node == item:
                        continue # prevent collecting the node twice (because they will get random names by default)
                    result[node.reference] = node.fileclass(node.serialize_toplevel())
                result[id] = item.fileclass(item.serialize_toplevel())
                files.update(result)

            elif isinstance(item, BeetFile): # TODO Check whether this works
                print("f") # DEBUG
                files[id] = item

        except Exception as exc:
            print(f"[red]Error compiling '{id}': {exc}[/red]")
            traceback.print_exc()
            errors.append(f"'{id}': {exc}")

    ctx.last_change_timestamp = time.time()
    ctx.last_error_message = "\n".join(errors) if errors else None
    ctx.latest_results = files
    return files


def rebuild_worker():
    """
    Wait for changes and then perform the calculation.
    A short debounce phase to prevent every single file operation from immediately
    triggering a full rebuild.
    """
    while not ctx.shutdown_event.is_set():
        ctx.rebuild_event.wait()

        if ctx.shutdown_event.is_set():
            break

        ctx.rebuild_event.clear()

        time.sleep(0.15)
        while ctx.rebuild_event.is_set():
            ctx.rebuild_event.clear()
            time.sleep(0.15)

        changed = list(ctx.changed_files)
        ctx.changed_files.clear()

        if any(f.endswith('.py') for f in changed):
            print("[#553bd9]RHOMBUS[reset]:  Checking for errors before reloading modules...")
            env = os.environ.copy()
            env["RHOMBUS_CHECK_ONLY"] = "1"
            
            # Check if the script runs without errors up to the start() call
            result = subprocess.run([sys.executable] + sys.argv, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                err_msg = result.stderr.strip() or result.stdout.strip()
                print(f"[red]RHOMBUS:  Failed to reload modules due to an error:[/red]\n\n{err_msg}\n")
                ctx.last_error_message = f"Failed to reload Python modules:\n{err_msg}"
                ctx.last_change_timestamp = time.time()
                continue

            print("[#553bd9]RHOMBUS[reset]:  Restarting process to reload modules...")
            if ctx.observer is not None:
                ctx.observer.stop()
            os._exit(42)

        with ctx.compile_lock:
            try:
                rebuild_all()
            except Exception as exc:
                ctx.last_error_message = repr(exc)


def start_watcher(path: str | Path):
    p = Path(path)
    observer = Observer()
    if p.is_file():
        observer.schedule(Handler(watch_file=p.name), str(p.parent), recursive=False)
    else:
        observer.schedule(Handler(), str(p), recursive=True)
    observer.start()
    ctx.observer = observer
    return observer


@service.on_event("startup")
def startup():
    start_watcher(ctx.watch_path)
    print(f"[#553bd9]RHOMBUS[reset]:  Preview service is now watching {ctx.watch_path}")
    sys.stdout.write("\033]0;Rhombus Preview Service\007")
    sys.stdout.flush()

    thread = threading.Thread(target=rebuild_worker, daemon=True)
    thread.start()

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
        "last_change": ctx.last_change_timestamp,
        "latest_data": [
            {
                "registry": "/".join(file.scope),
                "id": id,
                "content": file.encoder(file.data) if hasattr(file, "encoder") and hasattr(file, "data") else getattr(file, "text", str(file)),
                "language": getattr(file, "extension", ".json").lstrip("."),
            }
            for id, file in ctx.latest_results.items()
        ],
        "last_error": ctx.last_error_message,
    }

@service.get("/events")
async def get_events(request: fastapi.Request):
    async def event_generator():
        yield "retry: 500\n"
        yield "data: update\n\n"
        last_sent = ctx.last_change_timestamp
        while not ctx.shutdown_event.is_set():
            if await request.is_disconnected():
                break
            if ctx.last_change_timestamp != last_sent:
                last_sent = ctx.last_change_timestamp
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

@service.get("/addons/scripts")
def get_scripts():
    from rhombus.config import env
    from pathlib import Path
    return [{"name": Path(p).name, "url": f"/addons/scripts/{i}"} for i, p in enumerate(env.preview_scripts)]

@service.get("/addons/scripts/{index}")
def get_script_file(index: int):
    from rhombus.config import env
    from pathlib import Path
    try:
        p = Path(env.preview_scripts[index])
        if not p.is_file():
            return fastapi.responses.Response(status_code=404)
        mtype = "text/typescript" if p.suffix == ".ts" else "application/javascript"
        return fastapi.responses.FileResponse(p, media_type=mtype)
    except IndexError:
        return fastapi.responses.Response(status_code=404)


# Set the frontend endpoint just here, so it doesn't overtake the other endpoints
dist_dir = files("rhombus.preview").joinpath("dist")
service.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")


def start(
        watch_path: str | Path,
        /,
        *items: tuple[str, Density | RhombusASTNode | BeetFile],
        **uvicorn_args
    ) -> None:
    """Starts the Rhombus Preview service ASGI application.
    
    This includes the frontend and a file-watching backend. One can be used
    without the other or with other instance of the other.
    """
    if os.environ.get("RHOMBUS_CHECK_ONLY") == "1":
        return

    if not os.environ.get("RHOMBUS_SUPERVISOR_MODE"):
        import subprocess
        env = os.environ.copy()
        env["RHOMBUS_SUPERVISOR_MODE"] = "1"
        while True:
            proc = subprocess.Popen([sys.executable] + sys.argv, env=env)
            try:
                proc.wait()
            except KeyboardInterrupt:
                proc.wait()
                sys.exit(0)
            if proc.returncode == 42:
                continue
            sys.exit(proc.returncode)

    actual_items = []
    for item in items:
        actual_items.append(item)

    global ctx
    ctx = AppContext(watch_path=str(watch_path), items=actual_items)

    default_args = dict(
        host="127.0.0.1",
        port=8000
    )

    uvicorn.run(service, **uvicorn_args | default_args)


def resources_from_datapack(dp: beet.DataPack, *, types: list[DatapackResource]) -> list[tuple[str, Density | DatapackResource]]:
    """Gathers all density functions from a datapack as `Density` objects as
    well as datapack resources of given `DatapackResource` types.
    Use this function in the `items` parameter of `start_service` to preview
    an already compiled datapack.

    **NOTE:** If you are manually instanciating a `DataPack` from a directory,
    make sure to explicitely also load worldgen files, since they are are not
    loaded by Beet by default:
    ```
    import beet
    from beet.contrib.worldgen import WorldgenDensityFunction, WorldgenNoise
    from rhombus.support.lithostitched.fast_noise_config import LithostitchedFastNoiseConfig

    dp = beet.DataPack(
        path=path,
        extend_namespace=[
            WorldgenDensityFunction, WorldgenNoise,
            LithostitchedFastNoiseConfig
        ]
    )
    ```
    """
    dfs = []
    for typ in types:
        for id in list(dp[typ.fileclass]):
            dfs.append((id, typ.from_datapack(dp, id)))
    for id in list(dp[beet_worldgen.WorldgenDensityFunction]):
        dfs.append((id, Density.from_datapack(dp, id)))
    for id in list(dp[beet_worldgen.WorldgenNoiseSettings]):
        for noise_router in [
            "barrier", "continents", "depth", "erosion", "final_density", "fluid_level_floodedness", "fluid_level_spread",
            "lava", "preliminary_surface_level", "ridges", "temperature", "vegetation", "vein_gap", "vein_ridged", "vein_toggle"
        ]:
            df = Density.from_datapack_noise_router(dp, id, noise_router)
            if not isinstance(df.AST, (t.constant, t.Reference)):
                dfs.append((id + "/" + noise_router, df))
    return dfs