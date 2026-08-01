"""
For more information on the use and parameters, see `~.Noise`.
"""

__all__ = ["Noise", "noise", "old_blended_noise", "shifted_noise", "shift", "shift_a", "shift_b"]


from typing import ClassVar

from beet.contrib.worldgen import WorldgenNoise

from rhombus.core.datapack_resource import DatapackResource
from rhombus.core.utils import BeetFile
from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro
from rhombus.std.types import types


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
        return noise(self, xz_scale=xz_scale, y_scale=y_scale)


def noise(
    noise: Noise, xz_scale: float = 1, y_scale: float = 1
) -> Density[types.noise]:
    """Samples a noise.

    Parameters:
        noise (Noise): The noise to sample.
        xz_scale (float): Scales the X and Z coordinates before sampling.
        y_scale (float): Scales the Y coordinate before sampling.
            A `y_scale` of `0` will result in the noise sampled at `Y=0` for all `Y` of the density function, meaning that it effectively is 2D.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#noise)
    """
    return Density(types.noise(noise, xz_scale, y_scale))


def old_blended_noise(
    xz_scale: float,
    y_scale: float,
    xz_factor: float,
    y_factor: float,
    smear_scale_multiplier: float,
) -> Density[types.old_blended_noise]:
    """Samples a legacy noise.

    These noises are blocky in character, consisting of rectangular regions with varying value tendencies, interspersed with smaller, scattered structures.

    A scale of `1` corresponds to `12 blocks` of region width. At `0.5` the regions are almost indistinguishable.
    At higher scales, the repetition becomes clearly visible.
    Parameters:
        xz_scale (float between `0.001` and `1000.0`): Controls how often the block-like structures repeat in the XZ-plane.
        y_scale (float between `0.001` and `1000.0`): Controls how often the block-like structures repeat in the Y-axis.
        xz_factor (float between `0.001` and `1000.0`): Controls how much the small structures vary on the XZ-plane.
        y_factor (float between `0.001` and `1000.0`): Controls how much the small structures vary along the Y-axis.
        smear_scale_multiplier (float between `1.0` and `8.0`): Kinda affects how smooth the small structures are, but near to no impact on the structure.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#old_blended_noise)
    """
    return Density(
        types.old_blended_noise(
            xz_scale, y_scale, xz_factor, y_factor, smear_scale_multiplier
        )
    )


@macro
def shifted_noise(
    noise: Noise,
    xz_scale: float,
    y_scale: float,
    shift_x: AnyDensity,
    shift_y: AnyDensity,
    shift_z: AnyDensity,
) -> Density[types.shifted_noise]:
    """Samples a noise after shifting the input coordinates.

    Parameters:
        noise: Noise: The noise to sample.
        xz_scale (float): Scales the X and Z coordinates before sampling.
        y_scale (float): Scales the Y coordinate before sampling.
        shift_x (density function): Shifts the X coordinate before sampling.
        shift_y (density function): Shifts the Y coordinate before sampling.
        shift_z (density function): Shifts the Z coordinate before sampling.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#shifted_noise)
    """
    return Density(
        types.shifted_noise(
            noise, xz_scale, y_scale, shift_x.AST, shift_y.AST, shift_z.AST
        )
    )


def shift(argument: Noise) -> Density[types.shift]:
    """Samples a noise at `(x/4, y/4, z/4)`, then multiplies it by `4`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#shift)
    """
    return Density(types.shift(argument.AST))


def shift_a(argument: Noise) -> Density[types.shift_a]:
    """Samples a noise at `(x/4, 0, z/4)`, then multiplies it by `4`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#shift_a)
    """
    return Density(types.shift_a(argument.AST))


def shift_b(argument: Noise) -> Density[types.shift_b]:
    """Samples a noise at `(z/4, x/4, 0)`, then multiplies it by `4`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#shift_b)
    """
    return Density(types.shift_b(argument.AST))


# TODO: Re-add the implementation reference
def end_outer_islands() -> Density[types.end_outer_islands]:
    """Returns a value using a special noise algorithm used for outer end islands.
    The minimum value is set to `-0.84375`, the maximum value to `0.5625`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#end_islands) -
    """
    return Density(types.end_outer_islands())