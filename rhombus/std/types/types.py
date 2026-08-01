"""Vanilla density function types

These are the data models for the vanilla density function types.

They are not needed for normal use of the Rhombus language.
"""
from __future__ import annotations


from typing import ClassVar, Literal, TYPE_CHECKING
from rhombus.core import (
    RhombusASTNode,
    DensityFunction,
    SimpleDensityFunction,
    MappedDensityFunction,
    DoubleArgumentDensityFunction,
    Reference,
    constant,
    JSONDict,
)

if TYPE_CHECKING:
    from rhombus.std.noise import Noise

literal_number_limit: Literal[1000000] = 1000000.0
"""The maximum literal value allowed as a density function shorthand and
in the `argument` field of the `minecraft:constant` density function type.
"""
# This corresponds to net.minecraft.world.level.levelgen.DensityFunctions.NOISE_VALUE_CODEC


class autoCachedMappedFunctionBase(MappedDensityFunction):
    # We leave this for now.
    # @classmethod
    # def deserialize_toplevel(cls, data: JSONDict) -> Reference:
    #     definition = cls(DensityFunction.deserialize_inline(data["argument"]))
    #     return Reference("rhombus:partitioned/" + uuid_hash(definition.serialize_toplevel()), definition)
    ...


class abs(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:abs"


class add(DoubleArgumentDensityFunction):
    id: ClassVar[str] = "minecraft:add"

    def __repr__(self) -> str:
        return "(" + self.argument1.__repr__() + " + " + self.argument2.__repr__() + ")"


class beardifier(SimpleDensityFunction):
    id: ClassVar[str] = "minecraft:beardifier"


class blend_alpha(SimpleDensityFunction):
    id: ClassVar[str] = "minecraft:blend_alpha"


class blend_density(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:blend_density"


class blend_offset(SimpleDensityFunction):
    id: ClassVar[str] = "minecraft:blend_offset"


class cache_2d(autoCachedMappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_2d"


class cache_all_in_cell(autoCachedMappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_all_in_cell"


class cache_once(autoCachedMappedFunctionBase):
    id: ClassVar[str] = "minecraft:cache_once"


class clamp(DensityFunction):
    id: ClassVar[str] = "minecraft:clamp"
    input: DensityFunction  # no references
    min: float
    max: float


class cube(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:cube"


class distance_to_point(DensityFunction):
    id: ClassVar[str] = "minecraft:distance_to_point"
    point: tuple[int, int, int]
    metric: Literal["euclidean", "euclidean_squared", "manhattan", "chebyshev"]


# Deprecated
class end_islands(SimpleDensityFunction):
    id: ClassVar[str] = "minecraft:end_islands"


class end_outer_islands(SimpleDensityFunction):
    id: ClassVar[str] = "minecraft:end_outer_islands"


class find_top_surface(DensityFunction):
    id: ClassVar[str] = "minecraft:find_top_surface"
    density: DensityFunction
    upper_bound: DensityFunction
    lower_bound: int
    cell_height: int


class flat_cache(autoCachedMappedFunctionBase):
    id: ClassVar[str] = "minecraft:flat_cache"


class gradient(DensityFunction):
    id: ClassVar[str] = "minecraft:gradient"
    axis: Literal["x", "y", "z"]
    tiling: Literal["clamp_to_edge", "repeat", "mirrored_repeat"]
    from_coordinate: int
    to_coordinate: int # != from_coordinate
    from_value: float
    to_value: float

class half_negative(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:half_negative"


class interpolated(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:interpolated"


class interval_select(DensityFunction):
    id: ClassVar[str] = "minecraft:interval_select"
    input: DensityFunction
    thresholds: list[float]  # non-empty
    functions: list[DensityFunction]  # one Element more than thresholds


class invert(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:invert"


class log(DensityFunction):
    id: ClassVar[str] = "minecraft:log"
    input: DensityFunction


class max(DoubleArgumentDensityFunction):
    id: ClassVar[str] = "minecraft:max"


class min(DoubleArgumentDensityFunction):
    id: ClassVar[str] = "minecraft:min"


class mul(DoubleArgumentDensityFunction):
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


class pow(DensityFunction):
    id: ClassVar[str] = "minecraft:pow"
    base: DensityFunction
    exponent: DensityFunction

class quarter_negative(MappedDensityFunction):
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


class sign(DensityFunction):
    id: ClassVar[str] = "minecraft:sign"
    input: DensityFunction


class slice(DensityFunction):
    id: ClassVar[str] = "minecraft:slice"
    axis: Literal["x", "y", "z"]
    coordinate: int
    input: DensityFunction


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
                    DensityFunction.deserialize_inline(
                        {"type": "minecraft:spline", "spline": point["value"]}
                    )
                    if isinstance(point["value"], dict)
                    and point["value"].get("type") is None
                    else DensityFunction.deserialize_inline(point["value"]),
                    point["derivative"],
                )
                for point in data["spline"]["points"]
            ],
        )

    def serialize_toplevel(self) -> JSONDict:
        return {
            "type": self.id,
            "spline": {
                "coordinate": self.coordinate.serialize_inline(),
                "points": [
                    {
                        "location": point[0],
                        "value": point[1].serialize_inline()["spline"]
                        if isinstance(point[1], type(self))
                        else point[1].serialize_inline(),
                        "derivative": point[2],
                    }
                    for point in self.points
                ],
            },
        }

    @property
    def inscribed_toplevel_nodes(self) -> set[RhombusASTNode]:
        "Recursive search for all inscribed nodes, that will require a file when compiling"
        nodes = set()
        nodes |= self.coordinate.inscribed_toplevel_nodes
        for point in self.points:
            nodes |= point[1].inscribed_toplevel_nodes
        return nodes

    def show(self):
        "Only for debugging. Opens the spline in a pyplot."
        from rhombus.splines import show_spline

        if any((not isinstance(p[1], constant) for p in self.points)):
            raise ValueError("Can only show splines with numeric values")
        show_spline([(p[0], p[1].argument, p[2]) for p in self.points])


class square(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:square"


class sqrt(DensityFunction):
    id: ClassVar[str] = "minecraft:sqrt"
    input: DensityFunction
    

class squeeze(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:squeeze"


# Deprecated
class y_clamped_gradient(DensityFunction):
    id: ClassVar[str] = "minecraft:y_clamped_gradient"
    from_y: int
    to_y: int
    from_value: float
    to_value: float
