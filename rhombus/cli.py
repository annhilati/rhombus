from __future__ import annotations
from types import ModuleType
from typing import Callable
from pathlib import Path
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import argparse, sys, traceback, subprocess, shutil

import beet
from rhombus import Density
from rich import print

class RhombusCLIProblem(Exception): ...

def resolve_path_to_module(p: Path) -> ModuleType | None:

    spec = spec_from_file_location(p.stem, p)
    if spec is None:
        return None
    module = module_from_spec(spec)

    sys.modules[p.stem] = module

    assert spec.loader is not None
    spec.loader.exec_module(module)

    return module

def run_with_indent(cmd):
    from builtins import print
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        print(f"  {line}", end="")

    return process.wait()

def compile_project(source: Path, symbol: str = None, output_dir: Path = None, id: str = None) -> None:
    
    print("")
    print("[white on #5137d4] Rhombus Compilation [/white on #5137d4]")
    
    if not source.exists():
        raise RhombusCLIProblem(f"Path {source} does not exist")
    
    # Beet project directory
    if (source.is_file() and "beet" in source.name) or (not source.is_file() and any(p.is_file() and p.name.startswith("beet") for p in source.iterdir())):
        print(f"  Detected Beet project at {source}\n")
        run_with_indent(["beet"])
    
    # Python Module
    elif (module := resolve_path_to_module(source)) is not None:
        if symbol is None: raise RhombusCLIProblem("Missing parameter: symbol (after source)")
        if output_dir is None: raise RhombusCLIProblem("Missing parameter: --out")
        if id is None: raise RhombusCLIProblem("Missing parameter: --id")
        
        print(f"  Source: {source} :: {symbol}")
        print(f"  Output: {output_dir.resolve()}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with beet.DataPack(path=output_dir) as dp:
            
            target = getattr(module, symbol)
            
            if isinstance(target, Density):
                pass
            elif isinstance(target, Callable):
                target: Density = target()
            else:
                raise TypeError
            
            target.inject(dp, id)
            
    else:
        raise RhombusCLIProblem(f"Nothing to compile at path {source}")
    
    print("\n[#5137d4]── Done " + "─" * round(0.6 * shutil.get_terminal_size().columns - 10))


def rhombus_parser() -> argparse.ArgumentParser:
    CMD_rhombus = argparse.ArgumentParser(prog="rhombus")
    CMD_rhombus_SCMDs = CMD_rhombus.add_subparsers(dest="command", required=True)

    CMD_rhombus_compile = CMD_rhombus_SCMDs.add_parser("compile", help="Compile DSL files")
    CMD_rhombus_compile.add_argument("source",  type=Path)
    CMD_rhombus_compile.add_argument("symbol",  type=str,   default="main")
    CMD_rhombus_compile.add_argument("--out",   type=Path)
    CMD_rhombus_compile.add_argument("--id",    type=str)

    return CMD_rhombus


def main() -> None:
    
    try:
        parser = rhombus_parser()
        args = parser.parse_args()

        if args.command == "compile":
            compile_project(source=args.source, symbol=args.symbol, output_dir=args.out, id=args.id)
        
    except RhombusCLIProblem as e:
        print("")
        print(f"  [#62a8f0]Error")
        print(f"  [#62a8f0]╰─×[/#62a8f0] {str(e)}")
    
    except Exception as e:
        tb = e.__traceback__
        frames = traceback.extract_tb(tb)
        
        print("")
        print(f"  [red]Unexpected {type(e).__name__}")
        print(f"  [red]╰─×[/red] {str(e)}")
        
        first = frames[-1]
        second = frames[-2]
        print("")
        print(f"    [red]This was first issued in '{first.name}' ({first.filename}, line {first.lineno})")
        print(f"    [red]       {first.line}")
        print(f"    [red]Then passed on to        '{second.name}' ({second.filename}, line {second.lineno})")
        print(f"    [red]       {second.line}")