from typing import Literal
from rhombus.std import Density, macro, AnyDensity
from rhombus.support.lithostiched.fast_noise_config import FastNoiseConfig
from rhombus.support.lithostiched.types import Selection
from rhombus.support.lithostiched import types

__all__ = ["axis", "ceil", "cos", "fast_noise", "floor", "mix", "original_marker", "select", "shift", "sin", "sqrt", "wrapped_marker"]


def axis(axis: Literal["x", "y", "z"]):
    return Density(types.axis(axis))

@macro
def ceil(argument: AnyDensity):
    return Density(types.ceil(argument))

@macro
def cos(argument: AnyDensity):
    return Density(types.cos(argument))

@macro   
def fast_noise(config: FastNoiseConfig, xz_scale: float = 1.0, y_scale: float = 1.0, shift_x: AnyDensity = 0, shift_y: AnyDensity = 0, shift_z: AnyDensity = 0):
    return Density(types.fast_noise(config, xz_scale, y_scale, shift_x.AST, shift_y.AST, shift_z.AST))

@macro
def floor(argument: AnyDensity):
    return Density(types.floor(argument.AST))

@macro
def mix(input: AnyDensity, argument1: AnyDensity, argument2: AnyDensity):
    return Density(types.mix(input.AST, argument1.AST, argument2.AST))

def original_marker():
    return Density(types.original_marker())

@macro
def select(input: AnyDensity, fallback: AnyDensity, selections: list[Selection]):
    return Density(types.select(input.AST, fallback.AST, selections))

@macro
def shift(input: AnyDensity, shift_x: AnyDensity, shift_y: AnyDensity, shift_z: AnyDensity):
    return Density(types.shift(input.AST, shift_x.AST, shift_y.AST, shift_z.AST))

@macro
def sin(argument: AnyDensity):
    return Density(types.sin(argument.AST))

@macro
def sqrt(argument: AnyDensity):
    return Density(types.sqrt(argument.AST))

def wrapped_marker():
    return Density(types.wrapped_marker())