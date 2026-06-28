from typing import ClassVar, Literal, Optional

from beet.library.base import JsonFile, NamespaceFileScope

from rhombus.core.datapack_resource import DatapackResource
from rhombus.core.utils import JSONDict


class LithostichedFastNoiseConfig(JsonFile):
    """Class representing a Lithostiched noise configuration file."""

    scope: ClassVar[NamespaceFileScope] = ("lithostitched", "fast_noise_config")
    extension: ClassVar[str] = ".json"

class FastNoiseConfig(DatapackResource):
    """Defines a Lithostiched noise.
    
    **NOTE:** Because Lithostitched noises have a lot of interdependent fields, use
    these fabrics for instanciating:
    - `.SimplexNoise()`
    - `.CellularNoise()`
    - `.PerlinNoise()`
    - `.refer()`
    
    """
    fileclass: ClassVar = LithostichedFastNoiseConfig

    type: Literal["lithostitched:cellular", "lithostitched:perlin", "lithostitched:simplex"]
    frequency: float
    salt: int = None

    # lithostitched:cellular
    jitter:            float = None # between inclusive -1 and 1
    distance_function: Literal["euclidean", "euclidean_squared", "manhattan", "hybrid"] = None
    return_type:       Literal["cell_value", "distance", "distance_2", "distance_2_add", "distance_2_sub", "distance_2_mul", "distance_2_div"] = None
    # lithostitched:simplex
    fractal_type:      Literal["none", "fbm", "ridged", "ping_pong", "domain_warp_progressive", "domain_warp_independent"] = None
    octaves:           Optional[int] = None # non-negative, completely optional
    lacunarity:        Optional[float] = None # completely optional
    gain:              Optional[float] = None # completely optional

    def serialize_toplevel(self) -> JSONDict:
        return {
            "type": self.type,
            "frequency": self.frequency,
            **({"salt": self.salt} if self.salt is not None else {}),
            **({
                "jitter": self.jitter,
                "distance_function": self.distance_function,
                "return_type": self.return_type
            } if self.type == "lithostitched:cellular" else {}),
            **({
                "fractal_type": self.fractal_type,
                **({"octaves": self.octaves}       if self.octaves is not None else {}),
                **({"lacunarity": self.lacunarity} if self.lacunarity is not None else {}),
                **({"gain": self.gain}             if self.gain is not None else {}),
            } if self.type == "lithostitched:simplex" else {}),
        }
    
   
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
        return cls(type="lithostitched:simplex", frequency=frequency, salt=salt, fractal_type=fractal_type, octaves=octaves, lacunarity=lacunarity, gain=gain)
    
    @classmethod
    def CellularNoise(
        cls,
        frequency: float,
        jitter: float,
        distance_function: Literal["euclidean", "euclidean_squared", "manhattan", "hybrid"],
        return_type: Literal["cell_value", "distance", "distance_2", "distance_2_add", "distance_2_sub", "distance_2_mul", "distance_2_div"],
        salt: Optional[int] = None
    ) -> "FastNoiseConfig":
        return cls(type="lithostitched:cellular", frequency=frequency, salt=salt, jitter=jitter, distance_function=distance_function, return_type=return_type)
    
    @classmethod
    def PerlinNoise(cls, frequency: float, salt: int) -> "FastNoiseConfig":
        return cls(type="lithostitched:perlin", frequency=frequency, salt=salt)