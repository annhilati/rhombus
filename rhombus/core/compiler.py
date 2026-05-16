import os, sys, subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from beet.contrib.worldgen import WorldgenDensityFunction

from rhombus.core.datapack_resource import BeetFile
from rhombus.core.density_function import Reference, constant
from rhombus.core.node import RhombusASTNode


def compile(density: RhombusASTNode, identifier: str) -> dict[str, BeetFile]:
    

    files: dict[str, BeetFile] = {}

    root = density
    if ":" not in identifier: identifier = "minecraft:" + identifier

    files |= root.additional_described_files()
        
    files[identifier] = WorldgenDensityFunction(root.serialize(inline=False))

    return files

def show_in_temp(files: dict[str, BeetFile]) -> None:

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
            namespace = id.split(":")[0]
            name = id.split(":")[-1].replace("/", ".")
            p = path / (namespace + "." + f.scope[-1] + "." + name + f.extension)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f.encoder(f.data))

        open_folder(path)
        input("Press enter to let go the temporary directory ... ")