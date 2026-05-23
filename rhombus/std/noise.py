"""
For more information on the use and parameters, see `.Noise`.
"""

from typing import ClassVar

from beet.contrib.worldgen import WorldgenNoise

from rhombus.core.datapack_resource import DatapackResource
from rhombus.core.utils import BeetFile

__all__ = ["Noise"]


class Noise(DatapackResource):
    """Defines a perlin noise.

    **NOTE** To add a reference to an existing noise, use `.referenced()` instead.
    
    Parameters:
        firstOctave (int): Controls the base frequency of the noise. More negative values lead to more vast regions.<br>
            The scale in blocks over which the noise changes significantly is approximately `2^(-firstOctave)`.<br>
            E.g. `-9` corresponds to ~512 blocks between two oppositely polarized areas.

        amplitudes (list[float]): Controls how detailed the noise is.<br>
            Every amplitude adds an overlayed copy ("octave") of the noise half the scale of the octave before.<br>
            The magnitude of the amplitudes are relative weight factors. A `0` skips the octave.

    Fractal like amplitudes like `[1.0, 0.5, 0.25]` are considered especially natural.

    [Minecraft Wiki Reference](https://minecraft.wiki/w/Noise)
    """
 
    fileclass: ClassVar[type[BeetFile]] = WorldgenNoise

    firstOctave: int
    amplitudes:  list[float]

    def __post_init__(self):
        if self.amplitudes:
            self.amplitudes = [float(a) for a in self.amplitudes]
    
    def __repr__(self) -> str:
        if self.is_reference and self._reference is not None:
            return '"' + self.identifier + '"'
        return f"Noise({self.firstOctave}, {self.amplitudes!r})"