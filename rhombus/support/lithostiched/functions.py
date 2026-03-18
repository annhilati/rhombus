from typing import Literal
from rhombus.language.density import Density, builtinmacro, DensityDescriptor
from rhombus.support.lithostiched.fast_noise_config import FastNoiseConfig
from rhombus.support.lithostiched.types import Selection
from rhombus.support.lithostiched import types

__all__ = ["axis", "ceil", "cos", "fast_noise", "floor", "mix", "original_marker", "select", "shift", "sin", "sqrt", "wrapped_marker"]


def axis(axis: Literal["x", "y", "z"]):
    return Density(types.axis(axis))

@builtinmacro
def ceil(argument: DensityDescriptor):
    return DensityDescriptor(types.ceil(argument))

@builtinmacro
def cos(argument: DensityDescriptor):
    return DensityDescriptor(types.cos(argument))

@builtinmacro   
def fast_noise(config: FastNoiseConfig, xz_scale: float = 1.0, y_scale: float = 1.0, shift_x: DensityDescriptor = 0, shift_y: DensityDescriptor = 0, shift_z: DensityDescriptor = 0):
    return Density(types.fast_noise(config, xz_scale, y_scale, shift_x, shift_y, shift_z))

@builtinmacro
def floor(argument: DensityDescriptor):
    return DensityDescriptor(types.floor(argument))

@builtinmacro
def mix(input: DensityDescriptor, argument1: DensityDescriptor, argument2: DensityDescriptor):
    return DensityDescriptor(types.mix(input, argument1, argument2))

def original_marker():
    return Density(types.original_marker())

@builtinmacro
def select(input: DensityDescriptor, fallback: DensityDescriptor, selections: list[Selection]):
    return Density(types.select(input, fallback, selections))

@builtinmacro
def shift(input: DensityDescriptor, shift_x: DensityDescriptor, shift_y: DensityDescriptor, shift_z: DensityDescriptor):
    return Density(types.shift(input, shift_x, shift_y, shift_z))

@builtinmacro
def sin(argument: DensityDescriptor):
    return DensityDescriptor(types.sin(argument))

@builtinmacro
def sqrt(argument: DensityDescriptor):
    return DensityDescriptor(types.sqrt(argument))

def wrapped_marker():
    return Density(types.wrapped_marker())