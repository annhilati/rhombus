from __future__ import annotations
from types import ModuleType
from typing import Callable
from pathlib import Path
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import argparse, sys, traceback

import beet
from rhombus import Density
from rich import print

def resolve_path_to_module(p: Path) -> ModuleType:

    spec = spec_from_file_location(p.stem, p)
    module = module_from_spec(spec)

    sys.modules[p.stem] = module

    assert spec.loader is not None
    spec.loader.exec_module(module)

    return module

def compile_project(source: Path, symbol: str, output_dir: Path, id: str) -> None:
    
    print("")
    print("[white on #5137d4] Rhombus Compilation [/white on #5137d4]")
    print(f"  Source: {source} :: {symbol}")
    print(f"  Output: {output_dir}")
    print(f"  ID:     {id}")
    
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Compiling {source} -> {output_dir}")
    
    with beet.DataPack(path=output_dir) as dp:
        
        target = getattr(resolve_path_to_module(source), symbol)
        
        if isinstance(target, Density):
            pass
        elif isinstance(target, Callable):
            target: Density = target()
        else:
            raise TypeError
        
        target.inject(dp, id)
        
    print("Done")


def rhombus_parser() -> argparse.ArgumentParser:
    CMD_rhombus = argparse.ArgumentParser(prog="rhombus")
    CMD_rhombus_SCMDs = CMD_rhombus.add_subparsers(dest="command", required=True)

    CMD_rhombus_compile = CMD_rhombus_SCMDs.add_parser("compile", help="Compile DSL files")
    CMD_rhombus_compile.add_argument("source",  type=Path)
    CMD_rhombus_compile.add_argument("symbol",  type=str,   default="main")
    CMD_rhombus_compile.add_argument("--out",   type=Path,  required=True)
    CMD_rhombus_compile.add_argument("--id",    type=str,   required=True)

    return CMD_rhombus


def main() -> None:
    
    try:
        parser = rhombus_parser()
        args = parser.parse_args()

        if args.command == "compile":
            compile_project(args.source, args.symbol, args.out, args.id)
    
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