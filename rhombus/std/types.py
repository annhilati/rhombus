"""Vanilla density function types

These are the data models for the vanilla density function types.

They are not needed for normal use of the Rhombus language.
"""

from typing import ClassVar
from rhombus.core import (
    DensityFunction,
    SimpleFunctionBase,
    MappedFunctionBase,
    DoubleArgumentFunctionBase,
    Reference,
    constant,
    JSONDict,
    uuid_hash
)
from rhombus.std.noise import Noise

literal_number_limit: float = 10000000.0
"The maximum literal value allowed for shorthands for density functions and in the argument field of the `minecraft:constant` type"

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
    "shifted_noise", "spline",
    "square", "squeeze",
    "y_clamped_gradient"
]


class autoCachedMappedFunctionBase(MappedFunctionBase):
    
    @classmethod
    def deserialize_toplevel(cls, data: JSONDict) -> Reference:
        definition = cls(DensityFunction.deserialize_inline(data["argument"]))
        return Reference("rhombus:generated/" + uuid_hash(definition.serialize_toplevel()), definition)


class abs(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:abs" 

class add(DoubleArgumentFunctionBase): 
    id: ClassVar[str] = "minecraft:add"
    
    def __repr__(self) -> str:
        return "(" + self.argument1.__repr__() + " + " + self.argument2.__repr__() + ")"

class beardifier(SimpleFunctionBase):
    id: ClassVar[str] = "minecraft:beardifier"

class blend_alpha(SimpleFunctionBase):
    id: ClassVar[str] = "minecraft:blend_alpha"

class blend_density(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:blend_density"

class blend_offset(SimpleFunctionBase):
    id: ClassVar[str] = "minecraft:blend_offset"

class cache_2d(autoCachedMappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_2d"

class cache_all_in_cell(autoCachedMappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_all_in_cell"

class cache_once(autoCachedMappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_once"

class clamp(DensityFunction):
    id: ClassVar[str] = "minecraft:clamp"
    input: DensityFunction # no references
    min: float
    max:float

class cube(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:cube"

class end_islands(SimpleFunctionBase):
    id: ClassVar[str] = "minecraft:end_islands"

class find_top_surface(DensityFunction):
    id: ClassVar[str] = "minecraft:find_top_surface"
    density: DensityFunction
    upper_bound: DensityFunction
    lower_bound: int
    cell_height: int

class flat_cache(autoCachedMappedFunctionBase):
    id: ClassVar[str] = "minecraft:flat_cache"

class half_negative(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:half_negative"

class interpolated(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:interpolated"

class interval_select(DensityFunction):
    id: ClassVar[str] = "minecraft:interval_select"
    input: DensityFunction
    thresholds: list[float] # non-empty
    functions: list[DensityFunction] # one Element more that thresholds

class invert(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:invert"

class max(DoubleArgumentFunctionBase):
    id: ClassVar[str] = "minecraft:max"

class min(DoubleArgumentFunctionBase):
    id: ClassVar[str] = "minecraft:min"

class mul(DoubleArgumentFunctionBase):
    id: ClassVar[str] = "minecraft:mul"
    
    def __repr__(self) -> str:
        return "(" + self.argument1.__repr__() + " * " + self.argument2.__repr__() + ")"

class noise(DensityFunction):
    id: ClassVar[str] = "minecraft:noise"
    noise: Noise
    xz_scale: float
    y_scale: float

class old_blended_noise(DensityFunction):
    id: ClassVar[str] = "minecraft:old_blended_noise"
    xz_scale: float
    y_scale: float
    xz_factor: float
    y_factor: float
    smear_scale_multiplier: float

class quarter_negative(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:quarter_negative"

class range_choice(DensityFunction):
    id: ClassVar[str] = "minecraft:range_choice"
    input: DensityFunction
    min_inclusive: float
    max_exclusive: float
    when_in_range: DensityFunction
    when_out_of_range: DensityFunction

class shift(DensityFunction):
    id: ClassVar[str] = "minecraft:shift"
    argument: Noise

class shift_a(DensityFunction):
    id: ClassVar[str] = "minecraft:shift_a"
    argument: Noise

class shift_b(DensityFunction):
    id: ClassVar[str] = "minecraft:shift_b"
    argument: Noise

class shifted_noise(DensityFunction):
    id: ClassVar[str] = "minecraft:shifted_noise"
    noise: Noise
    xz_scale: float
    y_scale: float
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction

class spline(DensityFunction):
    id: ClassVar[str] = "minecraft:spline"
    coordinate: DensityFunction
    points: list[tuple[float, DensityFunction, float]]

    @classmethod
    def deserialize_toplevel(cls, data: JSONDict) -> "spline":
        return cls(
            DensityFunction.deserialize_inline(data["spline"]["coordinate"]),
            [
                (
                    point["location"],
                    DensityFunction.deserialize_inline({"type": "minecraft:spline", "spline": point["value"]})
                        if isinstance(point["value"], dict) and point["value"].get("type") is None
                        else DensityFunction.deserialize_inline(point["value"]),
                    point["derivative"]
                )
                for point in data["spline"]["points"]
            ]
        )
    
    def serialize_toplevel(self) -> JSONDict:
        return {
            "type": self.id,
            "spline": {
                "coordinate": self.coordinate.serialize_inline(),
                "points": [
                    {
                        "location": point[0],
                        "value": point[1].serialize_inline()["spline"] if isinstance(point[1].serialize_inline(), dict) else point[1].serialize_inline(),
                        "derivative": point[2], 
                    }
                    for point in self.points
                ]
            }
        }

    def show(self):
        "Only for debugging.<br>Open the spline in a pyplot."
        from rhombus.splines import show_spline
        if any((not isinstance(p[1], constant) for p in self.points)):
            raise ValueError("Can only show splines with numeric values")
        show_spline([(p[0], p[1].argument, p[2]) for p in self.points])
    
class square(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:square"

class squeeze(MappedFunctionBase):
    id: ClassVar[str] = "minecraft:squeeze"

class y_clamped_gradient(DensityFunction):
    id: ClassVar[str] = "minecraft:y_clamped_gradient"
    from_y: int
    to_y: int
    from_value: float
    to_value: float