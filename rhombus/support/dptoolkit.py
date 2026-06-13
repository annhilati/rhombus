"""Integration with the Datapack Toolkit ecosystem.

Provides utilities for reading and parsing Datapack Toolkit configuration files (dpconfig).
This ensures that Rhombus can interact seamlessly with automated datapack build processes.
"""

import beet
import yaml, json

def get_dpconfig(ctx: beet.Context) -> dict | None:
    root = ctx.directory

    data: dict | None = None

    for p in root.rglob("dpconfig.*"):
        with open(p, encoding="utf-8") as f:
            if p.suffix in [".yml", ".yaml"]:
                data = yaml.load(f, yaml.SafeLoader)
            elif p.suffix in [".json"]:
                data = json.loads(f.read())
        
    return data

# def write_dpconfig(ctx: beet.Context, data: dict) -> None:
#     if ctx.output_directory is None:
#         raise

#     ctx.output_directory.rglob("pack.mcmeta")[0].parent

#     with open(path, "w") as f:
#         yaml.dump(data, f)