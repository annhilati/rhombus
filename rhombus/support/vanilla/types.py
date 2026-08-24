from __future__ import annotations

from typing import ClassVar, Literal, TYPE_CHECKING

from rhombus.core import (
    DensityFunction,
    SimpleDensityFunction,
    MappedDensityFunction,
    DoubleArgumentDensityFunction,
    Reference,
    constant,
    JSONDict,
    field
)
from rhombus.core.environment import env

if TYPE_CHECKING:
    from rhombus.std.noise import Noise

literal_number_limit: Literal[1000000] = 1000000.0
"""The maximum literal value allowed as a density function shorthand and
in the `argument` field of the `minecraft:constant` density function type.
"""
# This corresponds to net.minecraft.world.level.levelgen.DensityFunctions.NOISE_VALUE_CODEC

_ = Reference, constant


class RoundingDensityFunction(MappedDensityFunction):
    multiple: DensityFunction


# ======// Model Classes //======================================================================//


class abs(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:abs"


class add(DoubleArgumentDensityFunction):
    id: ClassVar[str] = "minecraft:add"

    def __repr__(self) -> str:
        return "(" + self.left.__repr__() + " + " + self.right.__repr__() + ")"


class beardifier(SimpleDensityFunction):
    id: ClassVar[str] = "minecraft:beardifier"


class blend_alpha(SimpleDensityFunction):
    id: ClassVar[str] = "minecraft:blend_alpha"


class blend_density(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:blend_density"


class blend_offset(SimpleDensityFunction):
    id: ClassVar[str] = "minecraft:blend_offset"


class cache_2d(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:cache_2d"


class cache_all_in_cell(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:cache_all_in_cell"


class cache_once(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:cache_once"


class ceil(RoundingDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:ceil"


class clamp(DensityFunction):
    id: ClassVar[str] = "minecraft:clamp"
    input: DensityFunction = field(validate=lambda x: not isinstance(x, Reference) if env.datapack_version < 101.2 else True)
    min: float
    max: float


class cube(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:cube"
    
    def __repr__(self) -> str:
            return "(" + self.input.__repr__() + " ** 3)"


class distance_to_point(DensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:distance_to_point"
    point: tuple[int, int, int]
    metric: Literal["euclidean", "euclidean_squared", "manhattan", "chebyshev"]


class div(DoubleArgumentDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:div"


class end_outer_islands(SimpleDensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:end_outer_islands"


class find_top_surface(DensityFunction, versions=(82, ...)):
    id: ClassVar[str] = "minecraft:find_top_surface"
    density: DensityFunction
    upper_bound: DensityFunction
    lower_bound: int
    cell_height: int


class flat_cache(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:flat_cache"


class floor(RoundingDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:floor"


class gradient(DensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:gradient"
    axis: Literal["x", "y", "z"]
    tiling: Literal["clamp_to_edge", "repeat", "mirrored_repeat"]
    from_coordinate: int
    to_coordinate: int = field(validate=lambda x, df: x == df.from_coordinate)
    from_value: float
    to_value: float


class half_negative(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:half_negative"


class interpolated(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:interpolated"


class interval_select(DensityFunction, versions=(104, ...)):
    id: ClassVar[str] = "minecraft:interval_select"
    input: DensityFunction
    thresholds: list[float] = field(validate=lambda x: len(x) > 1)
    functions: list[DensityFunction] = field(validate=lambda x, df: len(x) == len(df.thresholds) + 1) # one Element more than thresholds


class lerp(DensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:lerp"
    alpha: DensityFunction
    first: DensityFunction
    second: DensityFunction


class log(MappedDensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:log"


class max(DoubleArgumentDensityFunction):
    id: ClassVar[str] = "minecraft:max"


class min(DoubleArgumentDensityFunction):
    id: ClassVar[str] = "minecraft:min"


class mul(DoubleArgumentDensityFunction):
    id: ClassVar[str] = "minecraft:mul"

    def __repr__(self) -> str:
        return "(" + self.left.__repr__() + " * " + self.right.__repr__() + ")"


class negate(MappedDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:negate"
    
    def __repr__(self) -> str:
                return "- " + self.input.__repr__()


class noise(DensityFunction):
    id: ClassVar[str] = "minecraft:noise"
    noise: Noise
    xz_scale: float
    y_scale: float


class old_blended_noise(DensityFunction):
    id: ClassVar[str] = "minecraft:old_blended_noise"
    xz_scale: float = field(added_with=10, validate=lambda x: 0.001 <= x <= 1000)
    y_scale: float = field(added_with=10, validate=lambda x: 0.001 <= x <= 1000)
    xz_factor: float = field(added_with=10, validate=lambda x: 0.001 <= x <= 1000)
    y_factor: float = field(added_with=10, validate=lambda x: 0.001 <= x <= 1000)
    smear_scale_multiplier: float = field(added_with=10, validate=lambda x: 1 <= x <= 8)


class pow(DensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:pow"
    base: DensityFunction
    exponent: DensityFunction
    
    def __repr__(self) -> str:
                return "(" + self.base.__repr__() + " ** " + self.exponent.__repr__() + ")"


class quarter_negative(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:quarter_negative"


class range_choice(DensityFunction):
    id: ClassVar[str] = "minecraft:range_choice"
    input: DensityFunction
    min_inclusive: float
    max_exclusive: float
    when_in_range: DensityFunction
    when_out_of_range: DensityFunction


class reciprocal(MappedDensityFunction, versions=(82, ...)):
    id: ClassVar[str] = field("minecraft:reciprocal", legacy_values={111.0: "minecraft:invert"})


class round(RoundingDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:round"


class shift(DensityFunction):
    id: ClassVar[str] = "minecraft:shift"
    noise: Noise = field(legacy_keys={111.0: "argument"})


class shift_a(DensityFunction):
    id: ClassVar[str] = "minecraft:shift_a"
    noise: Noise = field(legacy_keys={111.0: "argument"})


class shift_b(DensityFunction):
    id: ClassVar[str] = "minecraft:shift_b"
    noise: Noise = field(legacy_keys={111.0: "argument"})


class shifted_noise(DensityFunction):
    id: ClassVar[str] = "minecraft:shifted_noise"
    noise: Noise
    xz_scale: float
    y_scale: float
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction


class sign(MappedDensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:sign"


class slice(DensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:slice"
    axis: Literal["x", "y", "z"]
    coordinate: int
    input: DensityFunction


class spline(DensityFunction):
    id: ClassVar[str] = "minecraft:spline"
    coordinate: DensityFunction
    points: list[tuple[float, DensityFunction, float]]
    min_value: float = field(removed_with=10.0)
    max_value: float = field(removed_with=10.0)

    @classmethod
    def deserialize_toplevel(cls, data: JSONDict) -> "spline":
        kwargs = {}
        if "min_value" in data:
            kwargs["min_value"] = data["min_value"]
        if "max_value" in data:
            kwargs["max_value"] = data["max_value"]

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
            **kwargs
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
            **({
                "min_value": self.min_value,
                "max_value": self.max_value,
            } if env.datapack_version < 10.0 else {})
        }


    def show(self):
        "Only for debugging. Opens the spline in a pyplot."
        from rhombus.splines import show_spline

        if any((not isinstance(p[1], constant) for p in self.points)):
            raise ValueError("Can only show splines with numeric values")
        show_spline([(p[0], p[1].argument, p[2]) for p in self.points])


class square(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:square"
    
    def __repr__(self) -> str:
                return "(" + self.input.__repr__() + " ** 2)"


class sqrt(MappedDensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:sqrt"


class squeeze(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:squeeze"


class sub(DoubleArgumentDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:sub"


class truncate(RoundingDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:truncate"
