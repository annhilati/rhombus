from typing import ClassVar

from rhombus.core.density_function import MappedFunctionBase, DensityFunction
from rhombus.std.noise import Noise

class invert(MappedFunctionBase):
    id: ClassVar[str] = "tectonic:invert"

class config_constant(DensityFunction):
    id: ClassVar[str] = "tectonic:config_constant"
    key: str

class config_noise(DensityFunction):
    id: ClassVar[str] = "tectonic:config_noise"
    noise: Noise
    key: str
    shift_x: DensityFunction
    shift_z: DensityFunction