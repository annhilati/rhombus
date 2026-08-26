from typing import ClassVar, Literal

from rhombus.core import (
    DensityFunction,
    MappedDensityFunction,
    SimpleDensityFunction,
    field
)
from rhombus.std.noise import Noise


class end_islands(SimpleDensityFunction, versions=(9, 113)):
    id: ClassVar[str] = "minecraft:end_islands"


class cache_2d(MappedDensityFunction, versions=(9, 118)):
    id: ClassVar[str] = "minecraft:cache_2d"


class cache_all_in_cell(MappedDensityFunction, versions=(9, 118)):
    id: ClassVar[str] = "minecraft:cache_all_in_cell"


class flat_cache(MappedDensityFunction, versions=(9, 118)):
    id: ClassVar[str] = "minecraft:flat_cache"
    

class shifted_noise(DensityFunction, versions=(9, 118)):
    id: ClassVar[str] = "minecraft:shifted_noise"
    noise: Noise
    xz_scale: float
    y_scale: float
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction
    

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
    noise: Noise
    rarity_value_mapper: Literal["type_1", "type_2"]


class y_clamped_gradient(DensityFunction, versions=(9, 113)):
    id: ClassVar[str] = "minecraft:y_clamped_gradient"
    from_y: int = field(validate=lambda x: -4064 <= x <= 4062)
    to_y: int = field(validate=lambda x: -4064 <= x <= 4062)
    from_value: float
    to_value: float
