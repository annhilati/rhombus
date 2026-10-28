from __future__ import annotations

from typing import ClassVar, Literal, TYPE_CHECKING

from rhombus.core import (
    DensityFunction,
    SimpleDensityFunction,
    MappedDensityFunction,
    DoubleArgumentDensityFunction,
    Reference,
    constant,
    SubParameters,
    JSONDict,
    field,
)
from rhombus.runtime import rho

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


class beardifier(SimpleDensityFunction):
    id: ClassVar[str] = "minecraft:beardifier"


class blend_alpha(SimpleDensityFunction):
    id: ClassVar[str] = "minecraft:blend_alpha"


class blend_density(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:blend_density"


class blend_offset(SimpleDensityFunction):
    id: ClassVar[str] = "minecraft:blend_offset"


class cache(MappedDensityFunction):
    id: ClassVar[str] = field("minecraft:cache", legacy_values={118: "minecraft:cache_once"})


class ceil(RoundingDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:ceil"


class clamp(DensityFunction):
    id: ClassVar[str] = "minecraft:clamp"
    input: DensityFunction = field(validate=lambda x: not isinstance(x, Reference) if rho.datapack_version < 101.2 else True)
    min: float
    max: float


class cube(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:cube"
    

class distance_to_point(DensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:distance_to_point"
    point: tuple[int, int, int]
    metric: Literal["euclidean", "euclidean_squared", "manhattan", "chebyshev"]


class div(DoubleArgumentDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:div"


class domain_warp(DensityFunction, versions=(125.1, ...)):
    id: ClassVar[str] = "minecraft:domain_warp"
    input: DensityFunction
    offset_x: DensityFunction | None = field(None, validate=lambda x, df: any(o is not None for o in (df.offset_x, df.offset_y, df.offset_z)))
    offset_y: DensityFunction | None = None
    offset_z: DensityFunction | None = None


class end_outer_islands(SimpleDensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:end_outer_islands"


class find_top_surface(DensityFunction, versions=(82, ...)):
    id: ClassVar[str] = "minecraft:find_top_surface"
    density: DensityFunction
    upper_bound: DensityFunction
    lower_bound: int
    cell_height: int


class floor(RoundingDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:floor"


class VerticalAnchor(SubParameters):
    type: Literal["absolute", "above_bottom", "below_top", "relative_to_sea_level"]
    value: int = field(validate=lambda x: -2032 <= x <= 2031)

    @classmethod
    def Absolute(cls, height: int):
        return cls(type="absolute", value=height)

    @classmethod
    def Above_bottom(cls, height: int):
        return cls(type="above_bottom", value=height)

    @classmethod
    def Below_top(cls, depth: int):
        return cls(type="below_top", value=depth)

    @classmethod
    def Relative_to_sea_level(cls, height: int):
        return cls(type="relative_to_sea_level", value=height)

    def serialize_toplevel(self) -> JSONDict:
        return {
            self.type: self.value
        }

    @classmethod
    def deserialize_toplevel(cls, data: JSONDict):
        return cls(type=list(data.keys())[0], value=list(data.values())[0])

class gradient(DensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:gradient"
    axis: Literal["x", "y", "z"]
    tiling: Literal["clamp_to_edge", "repeat", "mirrored_repeat"]
    from_coordinate: int | VerticalAnchor = field(legacy_types={125.1: int}, validate=lambda x, df: False if isinstance(x, VerticalAnchor) and df.axis != "y" else True)
    to_coordinate: int | VerticalAnchor = field(legacy_types={125.1: int}, validate=lambda x, df: False if (isinstance(x, VerticalAnchor) and df.axis != "y") or x == df.from_coordinate else True)
    from_value: float
    to_value: float


class half_negative(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:half_negative"


class interval_select(DensityFunction, versions=(104, ...)):
    id: ClassVar[str] = "minecraft:interval_select"
    input: DensityFunction
    thresholds: list[float] = field(validate=lambda x: len(x) > 0)
    functions: list[DensityFunction] = field(validate=lambda x, df: len(x) == len(df.thresholds) + 1)


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


class negate(MappedDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:negate"
    

class noise(DensityFunction):
    id: ClassVar[str] = "minecraft:noise"
    noise: Noise
    xz_scale: float
    y_scale: float
    shift_x: DensityFunction = field(constant(0), added_with=118)
    shift_y: DensityFunction = field(constant(0), added_with=118)
    shift_z: DensityFunction = field(constant(0), added_with=118)


class old_blended_noise(DensityFunction, versions=(9, ...)):
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


class sign(MappedDensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:sign"


class slice(DensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:slice"
    input: DensityFunction
    axis: Literal["x", "y", "z"]
    coordinate: int


class SplinePoint(SubParameters):
    location: float
    value: DensityFunction | SplineConfig
    derivative: float

class SplineConfig(SubParameters):
    coordinate: DensityFunction
    points: list[SplinePoint]

class spline(DensityFunction):
    id: ClassVar[str] = "minecraft:spline"
    spline: SplineConfig
    min_value: float = field(removed_with=10.0, default=0.0)
    max_value: float = field(removed_with=10.0, default=0.0)

    def show(self):
        "Only for debugging. Opens the spline in a pyplot."
        from rhombus.std.math._splinelib import show_spline

        if any((not isinstance(p.value, constant) for p in self.spline.points)):
            raise ValueError("Can only show splines with numeric values")
        show_spline([(p.location, p.value.argument, p.derivative) for p in self.spline.points])


class square(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:square"
    

class sqrt(MappedDensityFunction, versions=(113, ...)):
    id: ClassVar[str] = "minecraft:sqrt"


class squeeze(MappedDensityFunction):
    id: ClassVar[str] = "minecraft:squeeze"


class sub(DoubleArgumentDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:sub"
    

class truncate(RoundingDensityFunction, versions=(111, ...)):
    id: ClassVar[str] = "minecraft:truncate"


class AxisScaling(SubParameters, versions=(125, ...)):
    mode: Literal["nearest_neighbor", "interpolate_linear", "interpolate_cosine", "interpolate_cubic", "b_spline_cubic"]
    cell_size: int = field(validate=lambda x: 1 <= x <= 64)

class upscale(DensityFunction, versions=(125, ...)):
    id: ClassVar[str] = "minecraft:upscale"
    input: DensityFunction
    x: AxisScaling
    y: AxisScaling
    z: AxisScaling