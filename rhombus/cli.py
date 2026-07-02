from pathlib import Path
from types import ModuleType
from typing import Any
import sys

from rich import print
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
        no_watch: bool = typer.Option(
            False,
            "--no-watch",
            "-n",
            help="Deactivates file watching.",
        )
    ):
    """Start the Rhombus preview service."""

    from rhombus import preview, env
    
    try:
        addons = [resolve_object_path(e) for e in addons]
        env.load(*addons)
    except Exception as e:
        raise typer.BadParameter(e)
    
    preview.serve(
        *preview.resources_from_datapack(
            path,
            additional_registries=env.preview_beet_file_extensions),
        watch_path=path if not no_watch else None
    )


def main() -> None:
    try:
        cli()
    # except RhombusCLIProblem as e:
    #     print(f"\n  [#62a8f0]Error[/#62a8f0]")
    #     print(f"  [#62a8f0]╰─×[/#62a8f0] {str(e)}")
    #     sys.exit(1)
        
    # except Exception as e:
    #     tb = e.__traceback__
    #     frames = traceback.extract_tb(tb)
        
    #     print(f"\n  [red]Unexpected {type(e).__name__}[/red]")
    #     print(f"  [red]╰─×[/red] {str(e)}")
        
    #     if len(frames) >= 2:
    #         first = frames[-1]
    #         second = frames[-2]
    #         print(f"\n    [red]This was first issued in '{first.name}' ({first.filename}, line {first.lineno})[/red]")
    #         print(f"    [red]       {first.line}[/red]")
    #         print(f"    [red]Then passed on to        '{second.name}' ({second.filename}, line {second.lineno})[/red]")
    #         print(f"    [red]       {second.line}[/red]")
    #     elif len(frames) == 1:
    #         first = frames[-1]
    #         print(f"\n    [red]This was issued in '{first.name}' ({first.filename}, line {first.lineno})[/red]")
    #         print(f"    [red]       {first.line}[/red]")
            
    #     sys.exit(1)
    except:
        raise


if __name__ == "__main__":
    main()