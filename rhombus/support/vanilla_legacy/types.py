"""'vdft' stands for 'vanilla density function types'.

These are the data models for the vanilla density function types.

They are not needed for normal use of the Rhombus language.
"""

from typing import ClassVar, Literal
from rhombus.core import (
    DensityFunction,
    MappedFunctionBase,
    MultiArgumentsFunctionBase
)
from rhombus.std import Noise

__all__ = [
    "slide",
    "terrain_shaper_spline"
]

class slide(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:slide"

class terrain_shaper_spline(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:terrain_shaper_spline"
    spline: Literal["offset", "factor", "jaggedness"]
    min_value: float
    max_value: float
    continentalness: DensityFunction
    erosion: DensityFunction
    weirdness: DensityFunction

class weird_scaled_sampler(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:weird_scaled_sampler"
    input: DensityFunction
    noise: Noise
    rarity_value_mapper: Literal["type_1", "type_2"]