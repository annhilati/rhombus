from typing import ClassVar
from rhombus.core.density_function import MappedFunctionBase, MultiArgumentsFunctionBase, DensityFunction
from rhombus.std.noise import Noise
from dataclasses import dataclass

class invert(MappedFunctionBase):
    id: ClassVar[str] = "tectonic:invert"

@dataclass(repr=False)
class config_constant(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "tectonic:config_constant"
    key: str

@dataclass(repr=False)
class config_noise(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "tectonic:config_noise"
    noise: Noise
    key: str
    shift_x: DensityFunction
    shift_z: DensityFunction