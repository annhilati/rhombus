from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Iterable
from importlib.resources import files
from contextlib import asynccontextmanager
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

from rhombus import Density
from rhombus.core import BeetFile, RhombusASTNode

def _get_relaunch_cmd():
    cmd = [sys.executable] + sys.argv
    if os.name == 'nt' and not sys.argv[0].endswith(('.py', '.exe')) and os.path.exists(sys.argv[0] + '.exe'):
        cmd = [sys.argv[0] + '.exe'] + sys.argv[1:]
    return cmd

class RhombusFilewatcher(FileSystemEventHandler):
    def __init__(self, service: RhombusPreviewService, watch_file: str | None = None):
        super().__init__()
        self.service = service
        self.last_events: dict[tuple[str, str], float] = {}
        self.watch_file = watch_file

    def _trigger(self, action: Literal["Created", "Deleted", "Changed", "Moved"], path: str):
        if self.watch_file and Path(path).name != self.watch_file:
            return

        now = time.time()
        key = (action, path)
        if key in self.last_events and (now - self.last_events[key]) < 0.2:
            return
        self.last_events[key] = now

        try:
            rel_path = Path(path).relative_to(self.service.watch_path)
        except ValueError:
            rel_path = Path(path).name

        print(f"[#35aaf3]WATCHER[reset]:  {action} {rel_path}")
        self.service.changed_files.add(path)
        self.service.last_change_timestamp = time.time()
        self.service.rebuild_event.set()

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


class RhombusPreviewService:
    def __init__(self, watch_path: Path | None, items: list[tuple[str, Density | RhombusASTNode | BeetFile]]):
        self.watch_path = watch_path
        self.items = items
        
        self.latest_results: dict[str, BeetFile] = {}
        self.changed_files: set[str] = set()

        self.last_change_timestamp: float | None = None
        self.last_error_message: str | None = None

        self.rebuild_event = threading.Event()
        self.shutdown_event = threading.Event()
        self.compile_lock = threading.Lock()

        self.observer: BaseObserver | None = None

        @asynccontextmanager
        async def lifespan(app: fastapi.FastAPI):
            self.startup()
            yield
            self.shutdown()

        self.app = fastapi.FastAPI(lifespan=lifespan)
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()

    def _setup_routes(self):
        self.app.add_api_route("/data", self.get_data, methods=["GET"])
        self.app.add_api_route("/events", self.get_events, methods=["GET"])
        self.app.add_api_route("/addons/scripts", self.get_scripts, methods=["GET"])
        self.app.add_api_route("/addons/scripts/{index}", self.get_script_file, methods=["GET"])
        
        dist_dir = files("rhombus.preview").joinpath("dist")
        self.app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")

    def rebuild_all(self) -> dict[str, Any]:
        files: dict[str, BeetFile] = {}
        errors: list[str] = []

        for (id, item) in self.items:
            try:
                if isinstance(item, Density):
                    result = item.compile(id)
                    files.update(result)
                    
                elif isinstance(item, RhombusASTNode):
                    result = {}
                    for node in item.inscribed_toplevel_nodes:
                        if node == item:
                            continue
                        result[node.reference] = node.fileclass(node.serialize_toplevel())
                    result[id] = item.fileclass(item.serialize_toplevel())
                    files.update(result)

                else:
                    # BeetFiles
                    files[id] = item

            except Exception as exc:
                print(f"[red]Error compiling '{id}': {exc}[/red]")
                traceback.print_exc()
                errors.append(f"'{id}': {exc}")

        self.last_change_timestamp = time.time()
        self.last_error_message = "\n".join(errors) if errors else None
        self.latest_results = files
        return files

    def rebuild_worker(self):
        """
        Wait for changes and then perform the calculation.
        A short debounce phase to prevent every single file operation from immediately
        triggering a full rebuild.
        """
        while not self.shutdown_event.is_set():
            self.rebuild_event.wait()

            if self.shutdown_event.is_set():
                break

            self.rebuild_event.clear()

            time.sleep(0.15)
            while self.rebuild_event.is_set():
                self.rebuild_event.clear()
                time.sleep(0.15)

            changed = list(self.changed_files)
            self.changed_files.clear()

            if any(f.endswith('.py') for f in changed):
                print("[#553bd9]RHOMBUS[reset]:  Checking for errors before reloading modules...")
                env = os.environ.copy()
                env["RHOMBUS_CHECK_ONLY"] = "1"
                
                # Check if the script runs without errors up to the start() call
                result = subprocess.run(_get_relaunch_cmd(), env=env, capture_output=True, text=True)
                if result.returncode != 0:
                    err_msg = result.stderr.strip() or result.stdout.strip()
                    print(f"[red]RHOMBUS:  Failed to reload modules due to an error:[/red]\n\n{err_msg}\n")
                    self.last_error_message = f"Failed to reload Python modules:\n{err_msg}"
                    self.last_change_timestamp = time.time()
                    continue

                print("[#553bd9]RHOMBUS[reset]:  Restarting process to reload modules...")
                if self.observer is not None:
                    self.observer.stop()
                os._exit(42)

            with self.compile_lock:
                try:
                    self.rebuild_all()
                except Exception as exc:
                    self.last_error_message = repr(exc)

    def start_watcher(self, path: Path):
        observer = Observer()
        if path.is_file():
            observer.schedule(RhombusFilewatcher(self, watch_file=path.name), str(path.parent), recursive=False)
        else:
            observer.schedule(RhombusFilewatcher(self), str(path), recursive=True)
        observer.start()
        self.observer = observer
        return observer

    def startup(self):
        if self.watch_path is not None:
            self.start_watcher(self.watch_path)
            print(f"[#553bd9]RHOMBUS[reset]:  Preview service is now watching {self.watch_path}")
        else:
            print(f"[#553bd9]RHOMBUS[reset]:  Preview service started (no file watching)")
        sys.stdout.write("\033]0;Rhombus Preview Service\007")
        sys.stdout.flush()

        thread = threading.Thread(target=self.rebuild_worker, daemon=True)
        thread.start()

        with self.compile_lock:
            self.rebuild_all()

    def shutdown(self):
        self.shutdown_event.set()
        self.rebuild_event.set()

        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            
    #======// Endpoints //=======================================================================//

    def get_data(self):
        return {
            "last_change": self.last_change_timestamp,
            "latest_data": [
                {
                    "registry": "/".join(file.scope),
                    "id": id,
                    "content": file.encoder(file.data) if hasattr(file, "encoder") and hasattr(file, "data") else getattr(file, "text", str(file)),
                    "language": getattr(file, "extension", ".json").lstrip("."),
                }
                for id, file in self.latest_results.items()
            ],
            "last_error": self.last_error_message,
        }

    async def get_events(self, request: fastapi.Request):
        async def event_generator():
            yield "retry: 500\n"
            yield "data: update\n\n"
            last_sent = self.last_change_timestamp
            while not self.shutdown_event.is_set():
                if await request.is_disconnected():
                    break
                if self.last_change_timestamp != last_sent:
                    last_sent = self.last_change_timestamp
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

    def get_scripts(self):
        from rhombus.core.config import env
        from pathlib import Path
        return [{"name": Path(p).name, "url": f"/addons/scripts/{i}"} for i, p in enumerate(env.preview_scripts)]

    def get_script_file(self, index: int):
        from rhombus.core.config import env
        from pathlib import Path
        try:
            p = Path(env.preview_scripts[index])
            if not p.is_file():
                return fastapi.responses.Response(status_code=404)
            mtype = "text/typescript" if p.suffix == ".ts" else "application/javascript"
            return fastapi.responses.FileResponse(p, media_type=mtype)
        except IndexError:
            return fastapi.responses.Response(status_code=404)


def serve(
        *items: tuple[str, Density | RhombusASTNode | BeetFile],
        watch_path: str | Path | None = Path.cwd(),
        **uvicorn_args: Any
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
            proc = subprocess.Popen(_get_relaunch_cmd(), env=env)
            try:
                while proc.poll() is None:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                proc.terminate()
                proc.wait()
                sys.exit(0)
            if proc.returncode == 42:
                continue
            sys.exit(proc.returncode)

    preview_service = RhombusPreviewService(watch_path=Path(watch_path) if watch_path is not None else None, items=[item for item in items])

    default_args = dict(
        host="127.0.0.1",
        port=8000,
        access_log=False
    )

    uvicorn.run(preview_service.app, **default_args | uvicorn_args)


def resources_from_datapack(dp: beet.DataPack | Path | str, *, additional_registries: Iterable[type[BeetFile]] = ()) -> list[tuple[str, BeetFile]]:
    """Gathers worldgen related resources from a datapack.
    Use this function in the `items` parameter of `service.start()` to preview
    an already compiled datapack.
    
    By default, `density_function`, `noise` and `noise_settings` are included.
    More registries can be extracted by providing an adequate Beet file class
    in `additional_registries`.
    """
    additional_registries = set(additional_registries) | {beet_worldgen.WorldgenDensityFunction, beet_worldgen.WorldgenNoiseSettings, beet_worldgen.WorldgenNoise}
    
    if isinstance(dp, (str, Path)):
        dp = beet.DataPack(path=dp, extend_namespace=additional_registries)
    
    files: set[tuple[str, BeetFile]] = set()
    
    for typ in additional_registries:
        for id in list(dp[typ]):
            files.add((id, dp[typ][id]))
    
    return files