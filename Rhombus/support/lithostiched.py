"""[Lithostiched](https://modrinth.com/mod/lithostitched) by Apollo"""

from dataclasses import dataclass
from typing import ClassVar, Literal, Optional
from Rhombus.core.density_function import MultiArgumentsFunctionBase, DensityFunction
from Rhombus.core.registry_resource import RegistryResource
from Rhombus.core.utils import JSONDict
from Rhombus.language.density import Density, BuiltinWizard

from beet.library.base import JsonFile, NamespaceFileScope

class LithostichedFastNoiseConfig(JsonFile):
    """Class representing a Lithostiched noise."""

    scope: ClassVar[NamespaceFileScope] = ("lithostitched", "fast_noise_config")
    extension: ClassVar[str] = ".json"

@dataclass(frozen=True)
class FastNoiseConfig(RegistryResource):
    """Defines a Lithostiched noise.
    
    **NOTE** Because Lithostiched noises have a lot of interdependent fields, use the fabrics instead.
    
    """
    fileclass: ClassVar = LithostichedFastNoiseConfig

    reference: Optional[str] = None

    type: Literal["lithostiched:cellular", "lithostiched:perlin", "lithostiched:simplex"]
    frequency: float
    salt: int = None

    # lithostiched:cellular
    jitter:            float = None # between inclusive -1 and 1
    distance_function: Literal["euclidean", "euclidean_squared", "manhattan", "hybrid"] = None
    return_type:       Literal["cell_value", "distance", "distance_2", "distance_2_add", "distance_2_sub", "distance_2_mul", "distance_2_div"] = None
    # lithostiched:simplex
    fractal_type:      Literal["none", "fbm", "ridged", "ping_pong", "domain_warp_progressive", "domain_warp_independent"] = None
    octaves:           Optional[int] = None # non-negaive, completely optional
    lacunarity:        Optional[float] = None # completely optional
    gain:              Optional[float] = None # completely optional

    def encode(self) -> JSONDict:
        return {
            "type": self.type,
            "frequency": self.frequency,
            **({"salt": self.salt} if self.salt is not None else {}),
            **({
                "jitter": self.jitter,
                "distance_function": self.distance_function,
                "return_type": self.return_type
            } if self.type == "lithostiched:cellular" else {}),
            **({
                "fractal_type": self.fractal_type,
                **({"octaves": self.octaves}       if self.octaves is not None else {}),
                **({"lacunarity": self.lacunarity} if self.lacunarity is not None else {}),
                **({"gain": self.gain}             if self.gain is not None else {}),
            } if self.type == "lithostiched:simplex" else {}),
        }
    
    @classmethod
    def decode(cls, dict: JSONDict) -> "FastNoiseConfig":
        return cls(
            **dict
        )

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

@dataclass(init=False)
class ReferenceFastNoiseConfig:
    """Returns a FastNoiseConfig with a reference to an externally provided noise.
    """

    def __new__(identifier: str, /) -> FastNoiseConfig:
        return FastNoiseConfig.as_pure_reference(identifier)
    
@dataclass(init=False)
class CellularNoise:

    def __new__(
        frequency: float,
        jitter: Optional[float],
        distance_function: Optional[Literal["euclidean", "euclidean_squared", "manhattan", "hybrid"]],
        return_type: Optional[Literal["cell_value", "distance", "distance_2", "distance_2_add", "distance_2_sub", "distance_2_mul", "distance_2_div"]],
        salt: Optional[int] = None
    ) -> FastNoiseConfig:
        return FastNoiseConfig(type="lithostiched:cellular", salt=salt, jitter=jitter, distance_function=distance_function, return_type=return_type)
    
@dataclass(init=False)
class SimplexNoise:

    def __new__(
        frequency: float,
        fractal_type: Literal["none", "fbm", "ridged", "ping_pong", "domain_warp_progressive", "domain_warp_independent"],
        octaves: Optional[int] = None, # non-negaive
        lacunarity: Optional[float] = None,
        gain: Optional[float] = None,
        salt: Optional[int] = None
    ) -> FastNoiseConfig:
        return FastNoiseConfig(type="lithostiched:simplex", salt=salt, fractal_type=fractal_type, octaves=octaves, lacunarity=lacunarity, gain=gain)
    

@BuiltinWizard   
def fast_noise(config: FastNoiseConfig, xz_scale: float = 1, y_scale: float = 1, shift_x: ... = 0, shift_y: ... = 0, shift_z: ... = 0):
    return Density(dft.fast_noise(config, xz_scale, y_scale, shift_x, shift_y, shift_z))