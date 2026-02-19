from dataclasses import dataclass
from typing import ClassVar
from Rhombus.core.density_function import MultiArgumentsFunctionBase, DensityFunction
from Rhombus.language.density import Density, BuiltinWizard, DensityDescriptor

from .fast_noise_config import FastNoiseConfig

class dft:

    @dataclass
    class fast_noise(MultiArgumentsFunctionBase):
        id: ClassVar[str] = "lithostiched:fast_noise"
        config: FastNoiseConfig
        xz_scale: float
        y_scale: float
        shift_x: DensityFunction
        shift_y: DensityFunction
        shift_z: DensityFunction

@BuiltinWizard   
def fast_noise(config: FastNoiseConfig, xz_scale: float = 1.0, y_scale: float = 1.0, shift_x: DensityDescriptor = 0, shift_y: DensityDescriptor = 0, shift_z: DensityDescriptor = 0):
    return Density(dft.fast_noise(config, xz_scale, y_scale, shift_x, shift_y, shift_z))