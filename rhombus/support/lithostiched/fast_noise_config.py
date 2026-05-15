from dataclasses import dataclass
from typing import ClassVar, Literal, Optional
from rhombus.core.datapack_resource import DatapackResource
from rhombus.core.utils import JSONDict

from beet.library.base import JsonFile, NamespaceFileScope

class LithostichedFastNoiseConfig(JsonFile):
    """Class representing a Lithostiched noise configuration file."""

    scope: ClassVar[NamespaceFileScope] = ("lithostitched", "fast_noise_config")
    extension: ClassVar[str] = ".json"

@dataclass
class FastNoiseConfig(DatapackResource):
    """Defines a Lithostiched noise.
    
    **NOTE** Because Lithostiched noises have a lot of interdependent fields, use these fabrics instead:
    - `.SimplexNoise()`
    - `.CellularNoise()`
    - `.PerlinNoise()`
    - `.referenced()`
    
    """
    fileclass: ClassVar = LithostichedFastNoiseConfig

    type: Literal["lithostiched:cellular", "lithostiched:perlin", "lithostiched:simplex"]
    frequency: float
    salt: int = None

    # lithostiched:cellular
    jitter:            float = None # between inclusive -1 and 1
    distance_function: Literal["euclidean", "euclidean_squared", "manhattan", "hybrid"] = None
    return_type:       Literal["cell_value", "distance", "distance_2", "distance_2_add", "distance_2_sub", "distance_2_mul", "distance_2_div"] = None
    # lithostiched:simplex
    fractal_type:      Literal["none", "fbm", "ridged", "ping_pong", "domain_warp_progressive", "domain_warp_independent"] = None
    octaves:           Optional[int] = None # non-negative, completely optional
    lacunarity:        Optional[float] = None # completely optional
    gain:              Optional[float] = None # completely optional

    reference: Optional[str] = None

    def serialize(self) -> JSONDict:
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
    def referenced(cls, identifier):
        return cls(reference=identifier, type=None, frequency=None)
    
    @classmethod
    def SimplexNoise(
        cls,
        frequency: float,
        fractal_type: Literal["none", "fbm", "ridged", "ping_pong", "domain_warp_progressive", "domain_warp_independent"],
        octaves: Optional[int] = None,
        lacunarity: Optional[float] = None,
        gain: Optional[float] = None,
        salt: Optional[int] = None
    ) -> "FastNoiseConfig":
        return cls(type="lithostiched:simplex", frequency=frequency, salt=salt, fractal_type=fractal_type, octaves=octaves, lacunarity=lacunarity, gain=gain)
    
    @classmethod
    def CellularNoise(
        cls,
        frequency: float,
        jitter: float,
        distance_function: Literal["euclidean", "euclidean_squared", "manhattan", "hybrid"],
        return_type: Literal["cell_value", "distance", "distance_2", "distance_2_add", "distance_2_sub", "distance_2_mul", "distance_2_div"],
        salt: Optional[int] = None
    ) -> "FastNoiseConfig":
        return cls(type="lithostiched:cellular", frequency=frequency, salt=salt, jitter=jitter, distance_function=distance_function, return_type=return_type)
    
    @classmethod
    def PerlinNoise(cls, frequency: float, salt: int) -> "FastNoiseConfig":
        return cls(type="lithostiched:perlin", frequency=frequency, salt=salt)