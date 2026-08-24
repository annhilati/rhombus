from pathlib import Path
from types import ModuleType
from typing import Any
import sys

import typer


cli = typer.Typer(
    help="The Rhombus CLI",
    add_completion=False,
)


class RhombusCLIProblem(Exception): ...


def resolve_object_path(path: str) -> Any:
    from importlib import import_module

    parts = path.split(".")

    for i in range(len(parts), 0, -1):
        try:
            module_name = ".".join(parts[:i])
            obj = import_module(module_name)

            for attr in parts[i:]:
                obj = getattr(obj, attr)

            return obj
        except ModuleNotFoundError as e:
            if not module_name.startswith(e.name):
                raise
            continue

    raise ImportError(f"Could not resolve object path '{path}'")


def resolve_path_to_module(p: Path) -> ModuleType | None:
    from importlib.util import spec_from_file_location, module_from_spec

    if not p.is_file() or p.suffix != ".py":
        return None

    spec = spec_from_file_location(p.stem, p)
    if spec is None:
        return None

    module = module_from_spec(spec)
    sys.modules[p.stem] = module

    assert spec.loader is not None
    spec.loader.exec_module(module)

    return module


@cli.command()
def help():
    pass


@cli.command("preview")
def preview(
    path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        help="Path to the datapack.",
    ),
    addons: list[str] = typer.Option(
        [],
        "--addon",
        "-a",
        help="Rhombus addon to load with the preview service. (Use multiple times to load multiple plugins)",
    ),
    overlays: list[str] = typer.Option(
        [],
        "--overlay",
        "-o",
        help="Datapack overlay to load. (Use multiple times to load multiple overlays)",
    ),
    no_watch: bool = typer.Option(
        False,
        "--no-watch",
        "-n",
        help="Deactivates file watching.",
    ),
):
    """Start the Rhombus preview service."""

    from rhombus import preview, env

    try:
        addons = [resolve_object_path(e) for e in addons]
        env.load_addons(*addons)
    except Exception as e:
        raise typer.BadParameter(e)

    preview.serve(
        *preview.resources_from_datapack(
            path,
            additional_registries=env.preview_beet_file_extensions,
            overlays=overlays,
        ),
        watch_path=path if not no_watch else None,
    )


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
