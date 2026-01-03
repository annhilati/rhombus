from dataclasses import fields
from pathlib import Path
from beet import Context
from beet.contrib.worldgen import WorldgenDensityFunction
from beet.core.file import DataModelBase


from rhombus.language.density import Density
from rhombus.core import *
from rhombus.core.df_types import Reference

def compile(density: Density, identifier: str) -> list[tuple[str, BeetFileClass]]:

    files: list[tuple[str, BeetFileClass]] = []

    root = density.wrapped
    if ":" not in identifier: identifier = "minecraft:" + identifier

    def search_for_additional_resources(o):
        if isinstance(o, DensityFunctionType):
            if isinstance(o, Reference) and o.default is not None:
                files.append((o.reference, WorldgenDensityFunction(o.encode())))
            for value in [getattr(o, param) for param in {f.name for f in fields(o) if f.init}]:
                search_for_additional_resources(value)
        elif isinstance(o, (list, tuple)):
            for value in o:
                search_for_additional_resources(value)
        elif isinstance(o, AdditionalResource):
            files.append((o.reference_identifier, o.fileclass(o.encode())))

    search_for_additional_resources(root)

    files.append((identifier, WorldgenDensityFunction(root.encode())))

    return files

def summon(files: list[tuple[str, BeetFileClass]], path: str | Path = "compiled") -> None:
    for id, f in files:
        p: Path = Path(path) / (id.replace(":", ".").replace("/", ".") + f.extension)
        p.parent.mkdir(parents=True, exist_ok=True)

        with open(p, mode="w") as io:
            io.write(f.encoder(f.data))

def inject(ctx: Context, density: Density, name: str):
    data = ctx.data


    files = compile(density, name)

    for id, file in files:
        data[id] = file
        print(f"Implemented {type(file).__name__} '{id}'")

        
    print(f"Finished implementing density function '{name}'")