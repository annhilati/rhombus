from typing import ClassVar, Literal
from dataclasses import dataclass
from Rhombus.core.density_function import MultiArgumentsFunctionBase, DensityFunction, MappedFunctionBase, SimpleFunctionBase
from Rhombus.core.sub_parameters import SubParameters
from .fast_noise_config import FastNoiseConfig

#======// Subparameters //=======================================================================//

@dataclass
class InclusiveRange(SubParameters):
    min_inclusive: float
    max_inclusive: float

@dataclass
class Selection(SubParameters):
    range: float | list[float] | InclusiveRange
    function: DensityFunction


#======// Density Function Classes //============================================================//

@dataclass
class axis(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "lithostitched:axis"
    axis: Literal["x", "y", "z"]

class ceil(MappedFunctionBase):
    id: ClassVar[str] = "lithostitched:ceil"

class cos(MappedFunctionBase):
    id: ClassVar[str] = "lithostitched:cos"

@dataclass
class fast_noise(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "lithostiched:fast_noise"
    config: FastNoiseConfig
    xz_scale: float
    y_scale: float
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction

class floor(MappedFunctionBase):
    id: ClassVar[str] = "lithostitched:floor"

@dataclass
class mix(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "lithostitched:mix"
    input: DensityFunction
    argument1: DensityFunction
    argument2: DensityFunction

class original_marker(SimpleFunctionBase):
    id: ClassVar[str] = "lithostitched:original_marker"

@dataclass
class select(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "lithostitched:select"
    input: DensityFunction
    fallback: DensityFunction
    selections: list[Selection]

@dataclass
class shift(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "lithostitched:shift"
    input: DensityFunction
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction

class sin(MappedFunctionBase):
    id: ClassVar[str] = "lithostitched:sin"

class sqrt(MappedFunctionBase):
    id: ClassVar[str] = "lithostitched:sqrt"

class wrapped_marker(SimpleFunctionBase):
    id: ClassVar[str] = "lithostitched:wrapped_marker"