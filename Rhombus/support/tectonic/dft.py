from typing import ClassVar
from Rhombus.core.density_function import MappedFunctionBase, MultiArgumentsFunctionBase, DensityFunction
from Rhombus.core.registry_resource import RegistryResource
from dataclasses import dataclass

class invert(MappedFunctionBase):
    id: ClassVar[str] = "tectonic:invert"

@dataclass
class config_constant(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "tectonic:config_constant"
    key: str

@dataclass
class config_noise(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "minecraft:noise"
    noise: RegistryResource
    key: str
    shift_x: DensityFunction
    shift_z: DensityFunction