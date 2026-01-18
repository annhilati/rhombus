from dataclasses import fields
from pathlib import Path
from beet import Context
from beet.contrib.worldgen import WorldgenDensityFunction

from rhombus.language.density import Density
from rhombus.core import *
from rhombus.core.df_types import Reference

def compile(density: Density, identifier: str) -> dict[str, BeetFileClass]:
    "For a `Density` object creates all Beet file instances needed. Use `summon()` additionally to have a look at them."
    files: dict[str, BeetFileClass] = {}

    root = density.wrapped
    if ":" not in identifier: identifier = "minecraft:" + identifier

    def search_for_additional_files(o):
        if isinstance(o, DensityFunctionType):
            if isinstance(o, Reference) and o.default is not None:
                files[o.reference] = WorldgenDensityFunction(o.default.encode())
            for value in [getattr(o, param) for param in {f.name for f in fields(o) if f.init}]:
                search_for_additional_files(value)
        elif isinstance(o, (list, tuple)):
            for value in o:
                search_for_additional_files(value)
        elif isinstance(o, AdditionalResource):
            files[o.reference_identifier] = o.fileclass(o.encode())

    search_for_additional_files(root)

    files[identifier] = WorldgenDensityFunction(root.encode())

    return files

def summon(files: dict[str, BeetFileClass], path: str | Path = Path.cwd() / "compiled") -> None:
    "Writes a bunch of Beet file instances to actual files."
    for id, f in files.items():
        p = Path(path) / (id.replace(":", ".").replace("/", ".") + f.extension)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, mode="w") as io:
            io.write(f.encoder(f.data))

def inject(ctx: Context, density: Density, name: str):
    "Implements a `Density` and all additionally needed files in a Beet datapack."
    data = ctx.data


    files = compile(density, name)

    for id, file in files.items():
        data[id] = file
        print(f"Implemented {type(file).__name__} '{id}'")

        
    print(f"Finished implementing density function '{name}'")