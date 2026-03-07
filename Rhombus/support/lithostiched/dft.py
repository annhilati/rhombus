from typing import ClassVar
from dataclasses import dataclass
from Rhombus.core.density_function import MultiArgumentsFunctionBase, DensityFunction, MappedFunctionBase
from .fast_noise_config import FastNoiseConfig

@dataclass
class fast_noise(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "lithostiched:fast_noise"
    config: FastNoiseConfig
    xz_scale: float
    y_scale: float
    shift_x: DensityFunction
    shift_y: DensityFunction
    shift_z: DensityFunction

# class axis
# class ceil
# class floor
# class sin
# class cos
# class sqrt
# class mix
# class shift
# class select