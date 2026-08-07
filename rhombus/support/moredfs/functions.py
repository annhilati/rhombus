__all__ = [
    "when_finite",
    "acos",
    "asin",
    "atan",
    "cbrt",
    "ceil",
    "clamp",
    "cos",
    "cosh",
    "derivative",
    "distance",
    "div",
    "dot_product",
    "floor",
    "floor_div",
    "floor_mod",
    "gapped_grid_square_spiral",
    "gradient_magnitude",
    "ieee_rem",
    "ln",
    "log",
    "log2",
    "log2_floor",
    "mod",
    "negate",
    "or_else",
    "polar_coords",
    "power",
    "profiler",
    "radius",
    "radius_3d",
    "reciprocal",
    "remainder",
    "resolver",
    "round",
    "shift",
    "sigmoid",
    "signum",
    "sin",
    "single_channel_image_tessellation",
    "sinh",
    "sqrt",
    "subtract",
    "tan",
    "tanh",
    "value_noise",
    "vector_angle",
    "x",
    "x_clamped_gradient",
    "y",
    "z",
    "z_clamped_gradient",
]

# For more detailed information about specific parameters, please refer to the MoreDFs documentation:
# https://github.com/TheDeathlyCow/more-density-functions/wiki
import base64
from typing import Literal

from PIL import Image
from rhombus.std.density import Density, AnyDensity; from rhombus.std.macros import macro
from rhombus.core import DensityFunction
from . import types
from .sub_parameters import (
    DistanceMetric,
    RandomSampler,
    ExtraOctaves,
    DerivativeComponent,
)


# ======// Coordinate Functions //==============================================================//


def x():
    "Returns the exact x-coordinate at the current position."
    return Density(types.x())


def y():
    "Returns the exact y-coordinate at the current position."
    return Density(types.y())


def z():
    "Returns the exact z-coordinate at the current position."
    return Density(types.z())


def x_clamped_gradient(from_x: int, to_x: int, from_value: float, to_value: float):
    "Creates a gradient along the x-axis between specified coordinates and values."
    return Density(types.x_clamped_gradient(from_x, to_x, from_value, to_value))


def z_clamped_gradient(from_z: int, to_z: int, from_value: float, to_value: float):
    "Creates a gradient along the z-axis between specified coordinates and values."
    return Density(types.z_clamped_gradient(from_z, to_z, from_value, to_value))


def polar_coords():
    "Computes the angle (radians) of the `(x, z)` position relative to `(0, 0)` using `atan2(x, z)`."
    return Density(types.polar_coords())


def radius():
    "Returns the Euclidean distance of the `(x, z)` position relative to `(0, 0)`."
    return Density(types.radius())


def radius_3d():
    "Returns the Euclidean distance of the `(x, y, z)` position relative to `(0, 0, 0)`."
    return Density(types.radius_3d())


@macro
def distance(
    distance_metric: DistanceMetric,
    point1: tuple[AnyDensity],
    point2: tuple[AnyDensity],
):
    "Computes distance between two n-dimensional points using a specific metric."
    p1 = [d.AST for d in point1] if point1 is not None else None
    p2 = [d.AST for d in point2] if point2 is not None else None
    return Density(types.distance(distance_metric, p1, p2))


# ======// Trigonometric Functions //===========================================================//


@macro
def acos(argument: AnyDensity):
    "Returns the arc cosine of the input (in radians)."
    return Density(types.acos(argument.AST))


@macro
def asin(argument: AnyDensity):
    "Returns the arc sine of the input (in radians)."
    return Density(types.asin(argument.AST))


@macro
def atan(argument: AnyDensity):
    "Returns the arc tangent of the input (in radians)."
    return Density(types.atan(argument.AST))


@macro
def cosh(argument: AnyDensity):
    "Returns the hyperbolic cosine of the input."
    return Density(types.cosh(argument.AST))


@macro
def sinh(argument: AnyDensity):
    "Returns the hyperbolic sine of the input."
    return Density(types.sinh(argument.AST))


@macro
def tanh(argument: AnyDensity):
    "Returns the hyperbolic tangent of the input."
    return Density(types.tanh(argument.AST))


@macro
def cos(argument: AnyDensity):
    "Returns the cosine of the input (radians)."
    return Density(types.cos(argument.AST))


@macro
def sin(argument: AnyDensity):
    "Returns the sine of the input (radians)."
    return Density(types.sin(argument.AST))


@macro
def tan(argument: AnyDensity):
    "Returns the tangent of the input (radians)."
    return Density(types.tan(argument.AST))


@macro
def vector_angle(argument1: AnyDensity, argument2: AnyDensity):
    "Returns the angle (radians) of `(arg1, arg2)` relative to `(0, 0)`."
    return Density(types.vector_angle(argument1.AST, argument2.AST))


# ======// Arithmetic Operations //=============================================================//


@macro
def cbrt(argument: AnyDensity):
    "Returns the cube root of the input."
    return Density(types.cbrt(argument.AST))


@macro
def div(numerator: AnyDensity, denominator: AnyDensity):
    "Returns numerator divided by denominator."
    return Density(types.div(numerator.AST, denominator.AST))


@macro
def floor_div(numerator: AnyDensity, denominator: AnyDensity):
    "Returns the floor of the division."
    return Density(types.floor_div(numerator.AST, denominator.AST))


@macro
def mod(numerator: AnyDensity, denominator: AnyDensity):
    "Returns the remainder of the division."
    return Density(types.mod(numerator.AST, denominator.AST))


@macro
def floor_mod(numerator: AnyDensity, denominator: AnyDensity):
    "Returns the floor'd modulo."
    return Density(types.floor_mod(numerator.AST, denominator.AST))


@macro
def ieee_rem(numerator: AnyDensity, denominator: AnyDensity):
    "Returns the IEEE 754 remainder."
    return Density(types.ieee_rem(numerator.AST, denominator.AST))


@macro
def negate(argument: AnyDensity):
    "Multiplies the input by -1."
    return Density(types.negate(argument.AST))


@macro
def power(base: AnyDensity, exponent: AnyDensity):
    "Returns base raised to the power of exponent."
    return Density(types.power(base.AST, exponent.AST))


@macro
def reciprocal(denominator: AnyDensity):
    "Returns the inverse (1/x) of the input."
    return Density(types.reciprocal(denominator.AST))


@macro
def sqrt(argument: AnyDensity):
    "Returns the square root of the input."
    return Density(types.sqrt(argument.AST))


@macro
def subtract(argument1: AnyDensity, argument2: AnyDensity):
    "Returns `argument1 - argument2`."
    return Density(types.subtract(argument1.AST, argument2.AST))


@macro
def remainder(numerator: AnyDensity, denominator: AnyDensity):
    "Returns the remainder."
    return Density(types.remainder(numerator.AST, denominator.AST))


# ======// Logarithmic Functions //=============================================================//


@macro
def log(argument: AnyDensity, base: AnyDensity):
    "Returns the logarithm of the argument in the specified base."
    return Density(types.log(argument.AST, base.AST))


@macro
def log2(argument: AnyDensity):
    "Returns the base-2 logarithm."
    return Density(types.log2(argument.AST))


@macro
def log2_floor(argument: AnyDensity):
    "Returns the floor of the base-2 logarithm (optimized)."
    return Density(types.log2_floor(argument.AST))


@macro
def ln(argument: AnyDensity):
    "Returns the natural logarithm (base e)."
    return Density(types.ln(argument.AST))


# ======// Rounding and Clamping //=============================================================//


@macro
def ceil(argument: AnyDensity):
    "Rounds up to the nearest integer."
    return Density(types.ceil(argument.AST))


@macro
def clamp(input: AnyDensity, min: float, max: float):
    "Clamps value between min and max."
    return Density(types.clamp(input.AST, min, max))


@macro
def floor(argument: AnyDensity):
    "Rounds down to the nearest integer."
    return Density(types.floor(argument.AST))


@macro
def round(argument: AnyDensity):
    "Rounds to the nearest integer."
    return Density(types.round(argument.AST))


@macro
def sigmoid(argument: AnyDensity):
    "Applies the sigmoid function (S-curve)."
    return Density(types.sigmoid(argument.AST))


@macro
def signum(argument: AnyDensity):
    "Returns -1 if x < 0, 0 if x = 0, 1 if x > 0."
    return Density(types.signum(argument.AST))


# ======// Calculus and Derivative Functions //=================================================//


@macro
def derivative(
    argument: AnyDensity,
    component_x: DerivativeComponent | None = None,
    component_y: DerivativeComponent | None = None,
    component_z: DerivativeComponent | None = None,
):
    "Returns the directional derivative."
    return Density(
        types.derivative(argument.AST, component_x, component_y, component_z)
    )


@macro
def gradient_magnitude(
    argument: AnyDensity,
    step_x: int | None = None,
    step_y: int | None = None,
    step_z: int | None = None,
):
    "Returns the magnitude of the gradient vector."
    return Density(types.gradient_magnitude(argument.AST, step_x, step_y, step_z))


@macro
def dot_product(
    argument1: AnyDensity,
    argument2: AnyDensity,
    step_x: int | None = None,
    step_y: int | None = None,
    step_z: int | None = None,
):
    "Returns the dot product of two functions."
    return Density(
        types.dot_product(argument1.AST, argument2.AST, step_x, step_y, step_z)
    )


# ======// Spatial Transformation & Noise //====================================================//


@macro
def shift(
    argument: AnyDensity, shift_x: AnyDensity, shift_y: AnyDensity, shift_z: AnyDensity
):
    "Evaluates `argument` at a shifted position."
    return Density(types.shift(argument.AST, shift_x.AST, shift_y.AST, shift_z.AST))


@macro
def value_noise(
    sampler: RandomSampler,
    size_x: int,
    size_y: int,
    size_z: int,
    interpolation: Literal["none", "lerp", "smoothstep"],
    salt: int | None = None,
    extra_octaves: ExtraOctaves | None = None,
):
    "Generates value noise with optional octaves, lacunarity, and persistence."
    return Density(
        types.value_noise(
            sampler, size_x, size_y, size_z, interpolation, salt, extra_octaves
        )
    )


# ======// Utility & Misc. Functions //=========================================================//


@macro
def or_else(argument: AnyDensity, fallback: AnyDensity):
    "Returns `argument` unless it's non-finite (NaN/Inf), then returns `fallback`."
    return Density(types.or_else(argument.AST, fallback.AST))


class when_finite:
    """Opens a new `or_else` fluent interface.

    ## Continuation

        **Declare a fallback value**
            `~.otherwise(AnyDensity)`
    """

    _subject: DensityFunction

    @macro
    def __init__(self, subject: AnyDensity):
        self._subject = subject.AST

    @macro
    def otherwise(self, value: AnyDensity) -> Density[types.or_else]:
        return or_else(self._subject, value.AST)


@macro
def resolver(argument: AnyDensity):
    "Internally memoizes and optimizes the density function tree."
    return Density(types.resolver(argument.AST))


@macro
def profiler(argument: AnyDensity, warm_up: int, iterations: int):
    "Profiles the performance of a density function and prints to console."
    return Density(types.profiler(argument.AST, warm_up, iterations))


@macro
def gapped_grid_square_spiral(
    tile_size: tuple[int, int],
    spacing: int,
    grid_cell_args: list[AnyDensity],
    when_out_of_bound: AnyDensity,
):
    """Creates a grid filled with density functions arranged in a spiral.

    The grid spans the XZ-plane (value is equal for all Y-coordinates).
    The first tile is oriented south-east of (0, 0), goes east first,
    then continues counter-clockwise.
    """
    args = [d.AST for d in grid_cell_args]
    return Density(
        types.gapped_grid_square_spiral(
            tile_size[0], tile_size[1], spacing, args, when_out_of_bound.AST
        )
    )


@macro
def single_channel_image_tessellation(image: str | Image.Image, size: tuple[int, int]):
    """Tiles a single-channel image across the world.

    `image` can be a base64-encoded string or a PIL image. In the latter case,
    it will be reduced to black-and-white before encoding.
    """
    if isinstance(image, Image.Image):
        import zlib

        image = image.convert("L")
        image = base64.b64encode(zlib.compress(image.tobytes())).decode("utf-8")
    return Density(types.single_channel_image_tessellation(size[0], size[1], image))
