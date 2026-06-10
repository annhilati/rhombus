__all__ = [
    "slide",
    "terrain_shaper_spline",
    "weird_scaled_sampler",
]


from typing import ClassVar, Literal

from rhombus.core import (
    DensityFunction,
    MappedFunctionBase
)
from rhombus.std import Noise

class slide(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:slide"

class terrain_shaper_spline(DensityFunction):
    id: ClassVar[str] = "minecraft:terrain_shaper_spline"
    spline: Literal["offset", "factor", "jaggedness"]
    min_value: float
    max_value: float
    continentalness: DensityFunction
    erosion: DensityFunction
    weirdness: DensityFunction

class weird_scaled_sampler(DensityFunction):
    id: ClassVar[str] = "minecraft:weird_scaled_sampler"
    input: DensityFunction
    noise: Noise
    rarity_value_mapper: Literal["type_1", "type_2"]