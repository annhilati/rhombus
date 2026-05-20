from typing import Literal
from rhombus.std import Density, builtinmacro, AnyDensity
from rhombus.support.lithostiched.fast_noise_config import FastNoiseConfig
from rhombus.support.lithostiched.types import Selection
from rhombus.support.lithostiched import types

__all__ = ["axis", "ceil", "cos", "fast_noise", "floor", "mix", "original_marker", "select", "shift", "sin", "sqrt", "wrapped_marker"]


def axis(axis: Literal["x", "y", "z"]):
    return Density(types.axis(axis))

@builtinmacro
def ceil(argument: AnyDensity):
    return Density(types.ceil(argument))

@builtinmacro
def cos(argument: AnyDensity):
    return Density(types.cos(argument))

@builtinmacro   
def fast_noise(config: FastNoiseConfig, xz_scale: float = 1.0, y_scale: float = 1.0, shift_x: AnyDensity = 0, shift_y: AnyDensity = 0, shift_z: AnyDensity = 0):
    return Density(types.fast_noise(config, xz_scale, y_scale, shift_x, shift_y, shift_z))

@builtinmacro
def floor(argument: AnyDensity):
    return Density(types.floor(argument))

@builtinmacro
def mix(input: AnyDensity, argument1: AnyDensity, argument2: AnyDensity):
    return Density(types.mix(input, argument1, argument2))

def original_marker():
    return Density(types.original_marker())

@builtinmacro
def select(input: AnyDensity, fallback: AnyDensity, selections: list[Selection]):
    return Density(types.select(input, fallback, selections))

@builtinmacro
def shift(input: AnyDensity, shift_x: AnyDensity, shift_y: AnyDensity, shift_z: AnyDensity):
    return Density(types.shift(input, shift_x, shift_y, shift_z))

@builtinmacro
def sin(argument: AnyDensity):
    return Density(types.sin(argument))

@builtinmacro
def sqrt(argument: AnyDensity):
    return Density(types.sqrt(argument))

def wrapped_marker():
    return Density(types.wrapped_marker())