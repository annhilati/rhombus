from typing import Literal
from rhombus.language import Density, builtinmacro, densityfunction
from rhombus.support.lithostiched.fast_noise_config import FastNoiseConfig
from rhombus.support.lithostiched.types import Selection
from rhombus.support.lithostiched import types

__all__ = ["axis", "ceil", "cos", "fast_noise", "floor", "mix", "original_marker", "select", "shift", "sin", "sqrt", "wrapped_marker"]


def axis(axis: Literal["x", "y", "z"]):
    return Density(types.axis(axis))

@builtinmacro
def ceil(argument: densityfunction):
    return Density(types.ceil(argument))

@builtinmacro
def cos(argument: densityfunction):
    return Density(types.cos(argument))

@builtinmacro   
def fast_noise(config: FastNoiseConfig, xz_scale: float = 1.0, y_scale: float = 1.0, shift_x: densityfunction = 0, shift_y: densityfunction = 0, shift_z: densityfunction = 0):
    return Density(types.fast_noise(config, xz_scale, y_scale, shift_x, shift_y, shift_z))

@builtinmacro
def floor(argument: densityfunction):
    return Density(types.floor(argument))

@builtinmacro
def mix(input: densityfunction, argument1: densityfunction, argument2: densityfunction):
    return Density(types.mix(input, argument1, argument2))

def original_marker():
    return Density(types.original_marker())

@builtinmacro
def select(input: densityfunction, fallback: densityfunction, selections: list[Selection]):
    return Density(types.select(input, fallback, selections))

@builtinmacro
def shift(input: densityfunction, shift_x: densityfunction, shift_y: densityfunction, shift_z: densityfunction):
    return Density(types.shift(input, shift_x, shift_y, shift_z))

@builtinmacro
def sin(argument: densityfunction):
    return Density(types.sin(argument))

@builtinmacro
def sqrt(argument: densityfunction):
    return Density(types.sqrt(argument))

def wrapped_marker():
    return Density(types.wrapped_marker())