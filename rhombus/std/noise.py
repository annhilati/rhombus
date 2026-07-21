"""
For more information on the use and parameters, see `~.Noise`.
"""

__all__ = ["Noise"]


from typing import ClassVar

from beet.contrib.worldgen import WorldgenNoise

from rhombus.core.datapack_resource import DatapackResource
from rhombus.core.utils import BeetFile


class Noise(DatapackResource):
    """Defines a perlin noise.

    **NOTE:** To reference an existing noise, use `~.refer()`.

    **NOTE:** The id of a noise affects the seed for calculation. To ensure that
    the seed does not change when modifying the values of the noise, use the
    following idiom to fix the id of the noise:
    ```
    n = "minecraft:be_fixed" @ Noise(-9, [1, 2, 3]) # respective your values
    ```

    Parameters:
        firstOctave (int): Controls the base frequency of the noise. More negative values lead to more vast regions.
            The scale in blocks over which the noise changes significantly is approximately `2^(-firstOctave)`.
            E.g. `-9` corresponds to ~512 blocks between two oppositely polarized areas.

        amplitudes (list[float]): Controls how detailed the noise is.
            Every amplitude adds an overlayed copy ("octave") of the noise half the scale of the octave before.
            The magnitude of the amplitudes are relative weight factors. A `0` skips the octave.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Noise) • [Wikipedia](https://en.wikipedia.org/wiki/Perlin_noise)
    """

    fileclass: ClassVar[type[BeetFile]] = WorldgenNoise

    firstOctave: int
    amplitudes: list[float]

    def __call__(self, xz_scale: float = 1, y_scale: float = 1):
        from rhombus.std.functions import noise

        return noise(self, xz_scale=xz_scale, y_scale=y_scale)
