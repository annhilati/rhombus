"""[Tectonic](https://modrinth.com/datapack/tectonic) by Apollo"""

from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from rhombus.core.df_types import MappedFunctionBase, MultiArgumentsFunctionBase, DensityFunctionTypeBase, DFType, decode_HOLDER_HELPER_CODEC
from rhombus.core.additional_resource import NEUAdditionalResource
from rhombus.language.density import Density, _arg_unwrapper
from rhombus.language.noise import Noise

class Invert(MappedFunctionBase):
    id: ClassVar[str] = "tectonic:invert"

@dataclass
class Config_constant(MultiArgumentsFunctionBase):
    id: ClassVar[str] = "tectonic:config_constant"
    key: str

@dataclass
class Config_noise(DensityFunctionTypeBase):
    id: ClassVar[str] = "minecraft:noise"
    noise: NEUAdditionalResource
    key: str
    shift_x: DFType
    shift_z: DFType

    @classmethod
    def decode(cls, data: dict) -> Config_noise:
        return cls(
            Noise(None, None, data["noise"]),
            data["key"],
            decode_HOLDER_HELPER_CODEC(data["shift_x"]),
            decode_HOLDER_HELPER_CODEC(data["shift_y"]),
        )

    def encode(self):
        return {
            "type": self.id,
            "noise": self.noise.reference_identifier,
            "key": self.key,
            "xz_scale": self.shift_x.encode(),
            "y_scale": self.shift_z.encode(),
        }

def invert(argument: Density | str | float) -> Density[Invert]:
    """Calculates `1/x`.
    """
    argument = _arg_unwrapper(argument)
    return Density(Invert(argument))

def config_constant(key: str) -> Density[Config_constant]:
    "References a constant from the Tectonic configuration."
    return Density(Config_constant(key))

def config_noise(noise: Noise, key: str, shift_x: Density | str | float, shift_z: Density | str | float) -> Density[Config_noise]:
    ""
    shift_x, shift_z = _arg_unwrapper(shift_x, shift_z)
    return Density(Config_noise(noise, key, shift_x, shift_z))