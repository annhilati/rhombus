from density.core.density import Density
from typing import Any
from uuid import uuid4
from beet import DataPack
from beet.contrib.worldgen import WorldgenDensityFunction, WorldgenNoise

# 
# FUNCTION IS YET UNTESTED
# 
def compile(density: Density, datapack: DataPack, location: str) -> None:
    """Compiles a density tree into a beet datapack"""

    raw = density.as_json()
    noise_namespace = location.split(":")[0]
    noises: dict[str, dict] = {}

    def implement_noises(o: dict | list | Any):
        if isinstance(o, dict):
            if o.get("type") in ["minecraft:noise", "minecraft:weird_scaled_noise", "minecraft:shifted_noise"]:
                noise = o["noise"]
                if isinstance(noise, dict):
                    if noise in [v for k, v in noises.items()]:
                        return o
                    key = noise_namespace + ":" + str(uuid4())
                    noises[key] = noise
                    return {k: v for k, v in o.items() if k != "noise"} | {"noise": key}
            return {k: implement_noises(v) for k, v in o.items()}

        elif isinstance(o, list):
            return [implement_noises(e) for e in o]
        
        else:
            return o
        
    datapack[location] = WorldgenDensityFunction(implement_noises(raw))
    for key, value in noises.items():
        datapack[key] = WorldgenNoise(value)