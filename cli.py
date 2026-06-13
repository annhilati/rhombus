from __future__ import annotations
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from types import ModuleType
from typing import Callable, Optional, Literal, Any
import sys, traceback, shutil, subprocess

from rhombus import Density
from rich import print
import beet
import typer

app = typer.Typer(
    help="The Rhombus CLI",
    add_completion=False,
)

class RhombusCLIProblem(Exception): ...


def resolve_path_to_module(p: Path) -> ModuleType | None:
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


def run_with_indent(cmd: list[str], dir: Path = None) -> int:
    from builtins import print as builtin_print
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=dir
    )

    if process.stdout:
        for line in process.stdout:
            builtin_print(f"  {line}", end="")

    return process.wait()

@app.command("help")
def help():
    print("TBA")

@app.command("compile")
def compile_project(
    mode: Literal["m", "b"] = typer.Argument(
        ...
    ),
    source: Path = typer.Argument(
        ..., 
        help="Path to a Beet project directory or a Python module."
    ),
    symbol: Optional[str] = typer.Argument(
        None,
        help="A Density in the regarding module or a nullary function returning one."
    ),
    outputdir: Optional[Path] = typer.Argument(
        None,
        help="Directory of the output datapack."
    ),
    target: Optional[str] = typer.Argument(
        None,
        help="Identifier used to implement the density function."
    )
    ) -> None:
    "Kompiliert ein Beet-Projekt oder ein Rhombus DSL Python-Modul."
    
    print("\n[white on #5137d4] Rhombus Compilation [/white on #5137d4]")
    
    if not source.exists():
        raise RhombusCLIProblem(f"Path {source} does not exist")
    
    
    if mode == "b":
        print("  [grey]Running with Beet...\n")
        run_with_indent(["beet"], source)
    
    elif mode == "m":
        print("  [grey]From a Python module...\n")
        
        if (module := resolve_path_to_module(source)) is None:
            raise RhombusCLIProblem (f"Path {source} is not a module")
        
        if symbol is None:
            raise RhombusCLIProblem ("Missing parameter symbol")
        try:
            symbol: Any = getattr(module, symbol)
        except AttributeError:
            raise RhombusCLIProblem(f"Symbol '{symbol}' not found in module '{source.stem}'")
        
        if outputdir is None:
            raise RhombusCLIProblem ("Missing parameter outputdir")
        if target is None:
            raise RhombusCLIProblem ("Missing parameter target")
    
        outputdir.mkdir(parents=True, exist_ok=True)
        if (
            len(list(outputdir.iterdir())) > 0
            and not any(p.is_file() and "pack.mcmeta" in p.name for p in outputdir.iterdir())
        ):
            raise RhombusCLIProblem(f"Directory {outputdir} is not empty, but also does not contain a datapack")

        if isinstance(symbol, Density):
            pass
        elif isinstance(symbol, Callable):
            symbol = symbol()
            if not isinstance(symbol, Density):
                raise TypeError(f"Callable '{symbol}' did not return a Density object.")
        else:
            raise TypeError(f"Symbol '{symbol}' is neither a Density nor a Callable returning one.")
        with beet.DataPack(path=outputdir) as dp:
            symbol.inject(dp, target)
            
    terminal_width = shutil.get_terminal_size().columns
    bar_length = max(10, round(0.6 * terminal_width - 10))
    print(f"\n[#5137d4]── Done " + "─" * bar_length + "[/#5137d4]")


def main() -> None:
    try:
        app()
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