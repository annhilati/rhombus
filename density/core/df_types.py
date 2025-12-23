from typing import Any, ClassVar, Literal
from dataclasses import dataclass, fields

# DensityExpression: TypeAlias = Any

class DensityFunctionTypeBase:
    """Base class for density function types.
    
    To add new types, create a sublass and set a ClassVar `id` or override the `as_json` method."""
    id: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": self.id,
            **{
                key: value.as_json() if getattr(value, "as_json", None) else value
                for key, value
                in {f.name: getattr(self, f.name) for f in fields(self)}.items()
            }
        }
    
    def __repr__(self):
        return f"{type(self).__name__}({", ".join([f'{key}={value}' for key, value in {f.name: getattr(self, f.name) for f in fields(self)}.items()])})"

@dataclass    
class Reference(DensityFunctionTypeBase):
    identifier: str
    
    def as_dict(self) -> str:
        return self.identifier

@dataclass
class abs(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:abs" 
    argument: Any

@dataclass
class add(DensityFunctionTypeBase): 
    id: ClassVar[str] = "minecraft:add"
    argument1: Any
    argument2: Any

@dataclass
class beardifier(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:beardifier"

@dataclass
class blend_alpha(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:blend_alpha"

@dataclass
class blend_density(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:blend_density"
    argument: Any

@dataclass
class blend_offset(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:blend_offset"

@dataclass
class cache_2d(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:cache_2d"
    argument: Any

@dataclass
class cache_all_in_cell(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:cache_all_in_cell"
    argument: Any

@dataclass
class cache_once(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:cache_once"
    argument: Any

@dataclass
class clamp(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:clamp"
    input: Any
    min: float
    max:float

@dataclass
class constant(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:constant"
    argument: float

    def as_dict(self):
        return self.argument

@dataclass
class cube(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:cube"
    argument: Any

@dataclass
class end_islands(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:end_islands"

@dataclass
class find_top_surface(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:find_top_surface"
    density: Any
    upper_bound: Any
    lower_bound: int
    cell_height: int

@dataclass
class flat_cache(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:flat_cache"
    argument: Any

@dataclass
class half_negative(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:half_negative"
    argument: Any

@dataclass
class interpolated(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:interpolated"
    argument: Any

@dataclass
class invert(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:invert"
    argument: Any

@dataclass
class max(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:max"
    argument1: Any
    argument2: Any

@dataclass
class min(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:min"
    argument1: Any
    argument2: Any

@dataclass
class mul(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:mul"
    argument1: Any
    argument2: Any

@dataclass
class noise(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:noise"
    noise: Any
    xz_scale: float
    y_scale: float

    def as_dict(self):
        return {
            "type": self.id,
            "noise": self.noise.reference if self.noise.reference is not None else self.noise.as_json(),
            "xz_scale": self.xz_scale,
            "y_scale": self.y_scale,
        }

@dataclass
class old_blended_noise(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:old_blended_noise"
    xz_scale: float
    y_scale: float
    xz_factor: float
    y_factor: float
    smear_scale_multiplier: float

@dataclass
class quarter_negative(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:quarter_negative"
    argument: Any

@dataclass
class range_choice(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:range_choice"
    input: Any
    min_inclusive: float
    max_exclusive: float
    when_in_range: Any
    when_out_of_range: Any

@dataclass
class shift(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:shift"
    argument: Any

@dataclass
class shift_a(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:shift_a"
    argument: Any

@dataclass
class shift_b(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:shift_b"
    argument: Any

@dataclass
class shifted_noise(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:shifted_noise"
    noise: Any
    xz_scale: float
    y_scale: float
    shift_x: Any
    shift_y: Any
    shift_z: Any

    def as_dict(self):
        if self.noise.reference is None:
            raise Exception
        return {
            "type": self.id,
            "noise": self.noise.reference,
            "xz_scale": self.xz_scale,
            "y_scale": self.y_scale,
            "shift_x": self.shift_x.value.as_json() if getattr(self.shift_x, "as_json", None) else self.shift_x,
            "shift_y": self.shift_y.value.as_json() if getattr(self.shift_y, "as_json", None) else self.shift_y,
            "shift_z": self.shift_z.value.as_json() if getattr(self.shift_z, "as_json", None) else self.shift_z,
        }

@dataclass
class slide(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:slide"
    argument: Any

@dataclass
class spline(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:spline"
    coordinate: Any
    points: list[tuple[float, float | Any, float]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": self.id,
            "spline": {
                "coordinate": self.coordinate,
                "points": [
                    {
                        "location": point[0],
                        "value": point[1].as_json() if getattr(point[1], "as_json", None) else point[1],
                        "derivative": point[2], 
                    }
                    for point in self.points
                ]
            }
        }

@dataclass
class square(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:square"
    argument: Any

@dataclass
class squeeze(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:squeeze"
    argument: Any

@dataclass
class terrain_shaper_spline(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:terrain_shaper_spline"
    spline: Literal["offset", "factor", "jaggedness"]
    min_value: float
    max_value: float
    continentalness: Any
    erosion: Any
    weirdness: Any

@dataclass
class weird_scaled_sampler(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:weird_scaled_sampler"
    rarity_value_mapper: Literal["type_1", "type_2"]
    noise: Any
    input: Any

    def as_dict(self):
        return {
            "type": self.id,
            "rarity_value_mapper": self.rarity_value_mapper,
            "noise": self.noise.reference if self.noise.reference is not None else ...,
            "input": self.input.value.as_json() if getattr(self.input, "as_json", None) else self.input,
        }

@dataclass
class y_clamped_gradient(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:y_clamped_gradient"
    from_y: int
    to_y: int
    from_value: float
    to_value: float