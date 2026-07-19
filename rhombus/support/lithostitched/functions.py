from typing import Literal

from rhombus.std import Density, AnyDensity, macro

from .fast_noise_config import FastNoiseConfig
from . import types

__all__ = [
    "axis",
    "ceil",
    "cos",
    "fast_noise",
    "floor",
    "mix",
    "original_marker",
    "select",
    "shift",
    "sin",
    "sqrt",
    "wrapped_marker",
]


def axis(axis: Literal["x", "y", "z"]):
    return Density(types.axis(axis))


@macro
def ceil(argument: AnyDensity):
    "Rounds the input to the nearest integer above the input."
    return Density(types.ceil(argument.AST))


@macro
def cos(argument: AnyDensity):
    "Returns the cosine value of the input."
    return Density(types.cos(argument.AST))


@macro
def fast_noise(
    config: FastNoiseConfig,
    xz_scale: float = 1.0,
    y_scale: float = 1.0,
    shift_x: AnyDensity = 0,
    shift_y: AnyDensity = 0,
    shift_z: AnyDensity = 0,
):
    """Samples a fast noise configuration.

    For more information on how to use fast noise, see `~..FastNoiseConfig`.

    ---
    [Lithostitched Wiki Reference](https://github.com/Apollounknowndev/lithostitched/wiki/Density-Function-Types#fast_noise)
    """
    return Density(
        types.fast_noise(
            config, xz_scale, y_scale, shift_x.AST, shift_y.AST, shift_z.AST
        )
    )


@macro
def floor(argument: AnyDensity):
    "Rounds the input to the nearest integer below the input."
    return Density(types.floor(argument.AST))


@macro
def mix(input: AnyDensity, argument1: AnyDensity, argument2: AnyDensity):
    """Smoothly transitions between `argument1` and `argument2` using `input` as the delta between them.

    When `input` is negative, returns `argument1`, when it is negative, returns `argument2`.

    ---
    [Lithostitched Wiki Reference](https://github.com/Apollounknowndev/lithostitched/wiki/Density-Function-Types#mix)
    """
    return Density(types.mix(input.AST, argument1.AST, argument2.AST))


def original_marker():
    return Density(types.original_marker())


@macro
def select(
    input: AnyDensity,
    fallback: AnyDensity,
    selections: list[tuple[float | tuple[float, float], AnyDensity]],
):
    """Selects a density function to return based on the given `input` function.

    Parameters:
        input (density function): Density function to match value ranges with.
        fallback (density function): Density function to return if no objects in `selections` match.
        selections (list[tuple[float | tuple[float, float], density function]]): List of ranges to match and density functions to return on match.

    ---
    [Lithostitched Wiki Reference](https://github.com/Apollounknowndev/lithostitched/wiki/Density-Function-Types#select)
    """
    selections = [(v, df.AST) for v, df in selections]
    return Density(types.select(input.AST, fallback.AST, selections))


@macro
def shift(
    input: AnyDensity,
    shift_x: AnyDensity = 0,
    shift_y: AnyDensity = 0,
    shift_z: AnyDensity = 0,
):
    "Returns the values of the input from shifted coordinates."
    return Density(types.shift(input.AST, shift_x.AST, shift_y.AST, shift_z.AST))


@macro
def sin(argument: AnyDensity):
    "Returns the sine value of the input."
    return Density(types.sin(argument.AST))


@macro
def sqrt(argument: AnyDensity):
    "Returns the square root of the input."
    return Density(types.sqrt(argument.AST))


def wrapped_marker():
    return Density(types.wrapped_marker())
