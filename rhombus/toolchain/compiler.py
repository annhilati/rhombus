from dataclasses import fields
from tempfile import TemporaryDirectory

from beet.contrib.worldgen import WorldgenDensityFunction
from rhombus.language.density import Density
from rhombus.core import *
from rhombus.core.df_types import Reference

def compile(density: Density, identifier: str) -> dict[str, BeetFileClass]:
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

def summon(files: dict[str, BeetFileClass]) -> None:
    import os, sys, subprocess
    from pathlib import Path

    def open_folder(path: Path) -> None:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])

    with TemporaryDirectory() as tmp:
        path = Path(tmp)

        for id, f in files.items():
            p = path / (id.replace(":", ".").replace("/", ".") + f.extension)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f.encoder(f.data))

        open_folder(path)
        input("Press enter to go on and delete the temporary directory ... ")
