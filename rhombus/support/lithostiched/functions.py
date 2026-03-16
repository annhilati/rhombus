from typing import Literal
from rhombus.language.density import Density, BuiltinWizard, DensityDescriptor
from rhombus.support.lithostiched.fast_noise_config import FastNoiseConfig
from rhombus.support.lithostiched.dft import Selection
from rhombus.support.lithostiched import dft

__all__ = ["axis", "ceil", "cos", "fast_noise", "floor", "mix", "original_marker", "select", "shift", "sin", "sqrt", "wrapped_marker"]


def axis(axis: Literal["x", "y", "z"]):
    return Density(dft.axis(axis))

@BuiltinWizard
def ceil(argument: DensityDescriptor):
    return DensityDescriptor(dft.ceil(argument))

@BuiltinWizard
def cos(argument: DensityDescriptor):
    return DensityDescriptor(dft.cos(argument))

@BuiltinWizard   
def fast_noise(config: FastNoiseConfig, xz_scale: float = 1.0, y_scale: float = 1.0, shift_x: DensityDescriptor = 0, shift_y: DensityDescriptor = 0, shift_z: DensityDescriptor = 0):
    return Density(dft.fast_noise(config, xz_scale, y_scale, shift_x, shift_y, shift_z))

@BuiltinWizard
def floor(argument: DensityDescriptor):
    return DensityDescriptor(dft.floor(argument))

@BuiltinWizard
def mix(input: DensityDescriptor, argument1: DensityDescriptor, argument2: DensityDescriptor):
    return DensityDescriptor(dft.mix(input, argument1, argument2))

def original_marker():
    return Density(dft.original_marker())

@BuiltinWizard
def select(input: DensityDescriptor, fallback: DensityDescriptor, selections: list[Selection]):
    return Density(dft.select(input, fallback, selections))

@BuiltinWizard
def shift(input: DensityDescriptor, shift_x: DensityDescriptor, shift_y: DensityDescriptor, shift_z: DensityDescriptor):
    return Density(dft.shift(input, shift_x, shift_y, shift_z))

@BuiltinWizard
def sin(argument: DensityDescriptor):
    return DensityDescriptor(dft.sin(argument))

@BuiltinWizard
def sqrt(argument: DensityDescriptor):
    return DensityDescriptor(dft.sqrt(argument))

def wrapped_marker():
    return Density(dft.wrapped_marker())