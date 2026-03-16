from typing import ClassVar, Literal
from dataclasses import dataclass
from rhombus.core.density_function import MappedFunctionBase, DoubleArgumentFunctionBase, SimpleFunctionBase, MultiArgumentsFunctionBase, DensityFunction, Reference, constant
from rhombus.core.utils import JSONDict
from rhombus.core.codec import decode_HOLDER_HELPER_CODEC
from rhombus.language.noise import Noise

__all__ = [
    "Reference", "constant",
    "abs", "add", "beardifier",
    "blend_alpha", "blend_density",
    "blend_offset", "cache_2d",
    "cache_all_in_cell", "cache_once",
    "clamp", "cube", "end_islands",
    "find_top_surface", "flat_cache",
    "half_negative", "interpolated",
    "invert", "max", "min", "mul",
    "noise", "old_blended_noise", 
    "quarter_negative", "range_choice",
    "shift", "shift_a", "shift_b",
    "shifted_noise", "slide",
    "spline", "square", "squeeze",
    "terrain_shaper_spline",
    "weird_scaled_sampler",
    "y_clamped_gradient"
]

class abs(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:abs" 

class add(DoubleArgumentFunctionBase): 
    id: ClassVar[str] = "minecraft:add"

class beardifier(SimpleFunctionBase):
    id: ClassVar[str] = "minecraft:beardifier"

class blend_alpha(SimpleFunctionBase):
    id: ClassVar[str] = "minecraft:blend_alpha"

class blend_density(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:blend_density"

class blend_offset(SimpleFunctionBase):
    id: ClassVar[str] = "minecraft:blend_offset"

class cache_2d(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_2d"

class cache_all_in_cell(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_all_in_cell"

class cache_once(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_once"

@dataclass
class clamp(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:clamp"
    input: DensityFunction # no references
    min: float
    max:float

class cube(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cube"

class end_islands(SimpleFunctionBase):
    id: ClassVar[str] = "minecraft:end_islands"

@dataclass
class find_top_surface(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:find_top_surface"
    density: DensityFunction
    upper_bound: DensityFunction
    lower_bound: int
    cell_height: int

class flat_cache(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:flat_cache"

class half_negative(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:half_negative"

class interpolated(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:interpolated"

class invert(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:invert"

class max(DoubleArgumentFunctionBase):
    id: ClassVar[str] = "minecraft:max"

class min(DoubleArgumentFunctionBase):
    id: ClassVar[str] = "minecraft:min"

class mul(DoubleArgumentFunctionBase):
    id: ClassVar[str] = "minecraft:mul"

@dataclass
class noise(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:noise"
    noise: Noise
    xz_scale: float
    y_scale: float

@dataclass
class old_blended_noise(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:old_blended_noise"
    xz_scale: float
    y_scale: float
    xz_factor: float
    y_factor: float
    smear_scale_multiplier: float

class quarter_negative(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:quarter_negative"

@dataclass
class range_choice(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:range_choice"
    input: DensityFunction
    min_inclusive: float
    max_exclusive: float
    when_in_range: DensityFunction
    when_out_of_range: DensityFunction

@dataclass
class shift(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:shift"
    argument: Noise

@dataclass
class shift_a(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:shift_a"
    argument: Noise

@dataclass
class shift_b(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:shift_b"
    argument: Noise

@dataclass
class shifted_noise(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:shifted_noise"
    noise: Noise
    xz_scale: float
    y_scale: float
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction

class slide(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:slide"

@dataclass
class spline(DensityFunction):
    id: ClassVar[str] = "minecraft:spline"
    coordinate: DensityFunction
    points: list[tuple[float, DensityFunction, float]]

    @classmethod
    def decode(cls, data: JSONDict) -> "spline":
        return cls(
            decode_HOLDER_HELPER_CODEC(data["spline"]["coordinate"]),
            [
                (
                    point["location"],
                    decode_HOLDER_HELPER_CODEC({"type": "minecraft:spline", "spline": point["value"]})
                        if isinstance(point["value"], dict) and point["value"].get("type") is None
                    else decode_HOLDER_HELPER_CODEC(point["value"]),
                    point["derivative"]
                )
                for point in data["spline"]["points"]
            ]
        )
    
    def encode(self) -> JSONDict:
        return {
            "type": self.id,
            "spline": {
                "coordinate": self.coordinate.encode(),
                "points": [
                    {
                        "location": point[0],
                        "value": point[1].encode(),
                        "derivative": point[2], 
                    }
                    for point in self.points
                ]
            }
        }

    def show(self):
        "Only for debugging.<br>Open the spline in a pyplot."
        from rhombus.macros._spline import show_spline
        if any((not isinstance(p[1], constant) for p in self.points)):
            raise Exception # TODO
        show_spline([(p[0], p[1].argument, p[2]) for p in self.points])
    
class square(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:square"

class squeeze(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:squeeze"

@dataclass
class terrain_shaper_spline(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:terrain_shaper_spline"
    spline: Literal["offset", "factor", "jaggedness"]
    min_value: float
    max_value: float
    continentalness: DensityFunction
    erosion: DensityFunction
    weirdness: DensityFunction

@dataclass
class weird_scaled_sampler(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:weird_scaled_sampler"
    rarity_value_mapper: Literal["type_1", "type_2"]
    noise: Noise
    input: DensityFunction

@dataclass
class y_clamped_gradient(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:y_clamped_gradient"
    from_y: int
    to_y: int
    from_value: float
    to_value: float