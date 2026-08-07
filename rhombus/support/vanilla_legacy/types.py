from typing import ClassVar, Literal

from rhombus.core import (
    DensityFunction,
    MappedDensityFunction,
    SimpleDensityFunction,
    JSONDict,
    field
)
from rhombus.std import noise


class end_islands(SimpleDensityFunction, versions=(9, 133)):
    id: ClassVar[str] = "minecraft:end_islands"


class slide(MappedDensityFunction, versions=(9, 10)):
    id: ClassVar[str] = "minecraft:slide"


class terrain_shaper_spline(DensityFunction, versions=(9, 10)):
    id: ClassVar[str] = "minecraft:terrain_shaper_spline"
    spline: Literal["offset", "factor", "jaggedness"]
    min_value: float
    max_value: float
    continentalness: DensityFunction
    erosion: DensityFunction
    weirdness: DensityFunction


class weird_scaled_sampler(DensityFunction, versions=(9, 104)):
    id: ClassVar[str] = "minecraft:weird_scaled_sampler"
    input: DensityFunction
    noise: noise.Noise
    rarity_value_mapper: Literal["type_1", "type_2"]


class y_clamped_gradient(DensityFunction, versions=(9, 113)):
    id: ClassVar[str] = "minecraft:y_clamped_gradient"
    from_y: int = field(validate=lambda x: -4064 <= x <= 4062)
    to_y: int = field(validate=lambda x: -4064 <= x <= 4062)
    from_value: float
    to_value: float
