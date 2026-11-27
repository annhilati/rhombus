"""Macros for working with noises."""

__all__ = [
    "Noise",
    "noise",
    "random",
    "random_seeded",
    "blended_noise",
    "shift",
    "shift_a",
    "shift_b",
    "end_outer_islands",
    "end_islands",
    "weird_scaled_sampler"
]

from typing import Literal
import uuid
import math as py_math

from rhombus.library.vanilla import types as vt, legacy_types as lt
from rhombus.std.builtin.density import Density, AnyDensity
from rhombus.std.builtin.macros import macro, implementation
from rhombus.std.builtin.dsl_config import DSLConfig, field
from rhombus.std.math import clamp, max, distributions
from rhombus.runtime import rho


class Noise(DSLConfig):
    """Defines a normal noise.

    **NOTE:** The id of a noise affects the seed for calculation. To ensure that
    the seed does not change when modifying the values of the noise, use the
    following idiom to fix the id of the noise:
    ```
    n = Noise(-9, [1, 2, 3]).named("minecraft:be_fixed")
    ```
    
    **TIP:** To reference an existing noise, use `~.refer()`.

    Parameters:
        base_octave (int): Formerly `firstOctave`. Controls the base frequency of the noise. More negative values lead to more vast regions.
            The scale in blocks over which the noise changes significantly is approximately `2^(-base_octave)`.
            E.g. `-9` corresponds to ~512 blocks between two oppositely polarized areas.
            If `legacy_random_source` in the noise settings is true, it must be an integer less than or equal to 1,
            otherwise the value range is not unlimited.

        amplitudes (list[float]): Controls how detailed the noise is.
            Every amplitude adds an overlayed copy ("octave") of the noise half the scale of the octave before.
            The magnitude of the amplitudes are relative weight factors. A `0` skips the octave.
            The length of this list implicitly defines the `octave_count` of the noise.

        base_amplitude (float): A scale factor applied to the noise output. Defaults to 1.0.
            If `normalize` is True, this is the expected amplitude of the final output.
            If `normalize` is False, this is the amplitude of the first octave.

        normalize (bool | Literal["legacy"]): Controls how the output amplitude should be normalized. Defaults to True.
            - `True`: `base_amplitude` determines the final output range.
            - `False`: `base_amplitude` only scales the first octave.
            - `"legacy"`: Inherits older normalization behavior (often smaller range).

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Noise) • [Wikipedia](https://en.wikipedia.org/wiki/Perlin_noise)
    """

    base_octave: int
    amplitudes: list[float]
    base_amplitude: float = 1.0
    normalize: bool | Literal["legacy"] = True
    _reference: str | None = field(default=None, init=False)
    
    
    @classmethod
    def refer(cls, identifier: str) -> Noise:
        # TODO: Standardize refering for DSLConfig and add back naming
        identifier = "minecraft:" + identifier if not ":" in identifier else identifier
        instance = Noise(base_octave=None, amplitudes=None)
        instance._reference = identifier
        return instance


    def build(self) -> vt.NoiseDefinition:
        
        if self._reference is not None:
            return vt.NoiseDefinition.refer(self._reference)
        
        if rho.datapack_version is not None and rho.datapack_version < 113:
            return vt.NoiseDefinition(base_octave=self.base_octave, amplitude_modifiers=self.amplitudes) 

        return vt.NoiseDefinition(
            base_octave=self.base_octave,
            base_amplitude=self.base_amplitude,
            normalize=self.normalize,
            octave_count=len(self.amplitudes),
            amplitude_modifiers=self.amplitudes if any(a != 1.0 for a in self.amplitudes) else []
        )


# TODO: Rename to sample?
@macro
def noise(
    noise: Noise,
    xz_scale: float = 1,
    y_scale: float = 1,
    shift_x: AnyDensity = 0,
    shift_y: AnyDensity = 0,
    shift_z: AnyDensity = 0,
) -> Density:
    """Samples a noise.

    Parameters:
        noise (Noise): The noise to sample.
        xz_scale (float): Scales the X and Z coordinates before sampling.
        y_scale (float): Scales the Y coordinate before sampling.
            A `y_scale` of `0` will result in the noise sampled at `Y=0` for all `Y` of the density function, meaning that it effectively is 2D.
        shift_x (density function): Shifts the X coordinate before sampling.
        shift_y (density function): Shifts the Y coordinate before sampling.
        shift_z (density function): Shifts the Z coordinate before sampling.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#noise)
    """
    @implementation(until=113)
    def noise_legacy():
        if shift_x.AST == shift_y.AST == shift_z.AST == Density(0).AST:
            return Density(vt.noise(noise.build(), xz_scale, y_scale))
        return Density(lt.shifted_noise(noise.build(), xz_scale, y_scale, shift_x.build(), shift_y.build(), shift_z.build()))
    
    @implementation
    def noise_modern():
        return Density(vt.noise(noise.build(), xz_scale, y_scale, shift_x.build(), shift_y.build(), shift_z.build()))


def blended_noise(
    xz_scale: float,
    y_scale: float,
    xz_factor: float,
    y_factor: float,
    smear_scale_multiplier: float,
) -> Density:
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
        vt.old_blended_noise(
            xz_scale, y_scale, xz_factor, y_factor, smear_scale_multiplier
        )
    )


@macro
def shift(argument: Noise) -> Density:
    """Samples a noise at `(x/4, y/4, z/4)`, then multiplies it by `4`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#shift)
    """
    return Density(vt.shift(argument.build()))


@macro
def shift_a(argument: Noise) -> Density:
    """Samples a noise at `(x/4, 0, z/4)`, then multiplies it by `4`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#shift_a)
    """
    return Density(vt.shift_a(argument.build()))


@macro
def shift_b(argument: Noise) -> Density:
    """Samples a noise at `(z/4, x/4, 0)`, then multiplies it by `4`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#shift_b)
    """
    return Density(vt.shift_b(argument.build()))


@macro
def end_outer_islands() -> Density:
    """Samples a noise using a
    [special algorithm](https://mcsrc.dev/2/26.3/net/minecraft/world/level/levelgen/densityfunction/generator/EndIslandFunction#L52)
    that is used for the outer end islands. The minimum value is set to `-0.84375`,
    the maximum value to `0.5625`.
    
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#end_outer_islands)
    """
    @implementation(since=113)
    def end_outer_islands():
        return Density(vt.end_outer_islands())


@macro
def end_islands() -> Density:
    """Samples a noise using a
    [special algorithm](https://mcsrc.dev/2/26.2/net/minecraft/world/level/levelgen/DensityFunctions#L532)
    that is used for the outer end islands. The minimum value is set to `-0.84375`,
    the maximum value to `0.5625`.
    """
    @implementation(until=113)
    def legacy():
        return Density(lt.end_islands())

    @implementation
    def modern():
        from rhombus.std.coords import distance_to_point, slice
        dist = distance_to_point((0, 0, 0), metric="euclidean")
        inner = (clamp(100.0 - dist, min=-100.0, max=80.0) - 8.0) * (1 / 128)
        inner_slice = slice(inner, y=0)
            
        return max(inner_slice, end_outer_islands())
    
    
@macro
def weird_scaled_sampler(
    input: AnyDensity,
    noise: Noise,
    rarity_value_mapper: Literal["type_1", "type_2"],
) -> Density:
    @implementation(until=104)
    def legacy():
        return Density(lt.weird_scaled_sampler(
            input=input.build(),
            noise=noise.build(),
            rarity_value_mapper=rarity_value_mapper,
        ))

    @implementation
    def modern():
        from rhombus.std.math import abs
        from rhombus.std.conditional import interval_select
        if rarity_value_mapper == "type_1":
            thresholds = [-0.5, 0.0, 0.5]
            factors = [0.75, 1.0, 1.5, 2.0]
        else: # type_2
            thresholds = [-0.75, -0.5, 0.5, 0.75]
            factors = [0.5, 0.75, 1.0, 2.0, 3.0]

        functions = [
            factor * abs(Density(noise(
                xz_scale=1.0 / factor,
                y_scale=1.0 / factor,
            )))
            for factor in factors
        ]

        return Density(interval_select(
            input=input.build(),
            thresholds=thresholds,
            functions=functions,
        ))
        
        
# ======// Random Samplers //================================================================//


# TODO: make uniform distribution optional?
@macro
def random(a: AnyDensity = 0, b: AnyDensity = 1, *, key: str = ...) -> Density:
    """Returns a uniformly random number that is different for all coordinates.
    
    **ATTENTION:** Every call to this function produces a new independent random generator.
    To use the same random generator twice without using a transient variable, set the `key` parameter equally.
    """
    # NOTE: The order of a and b is irrelevant
    key = key if key is not ... else str(uuid.uuid4()).replace("-", "")
    if not ":" in key:
        key = "rhombus:generated/" + key
        
    # We sample a noise whose values differ significantly for each block without following a pattern
    n = noise(Noise(0, [1], base_amplitude=1, normalize=True).named(key), xz_scale=1, y_scale=1)
    
    sqrt2 = py_math.sqrt(2)
    
    # The noise's values are distributed normally with a standard deviation of 1/3.
    # We perform Inverse Transform Sampling to redistribute the random values uniformly.
    return a + (b - a) * (1/2 + (distributions.erf(3/sqrt2 * n)) / (2 * py_math.erf(3/sqrt2)))


@macro
def random_seeded(a: AnyDensity = 0, b: AnyDensity = 1, *, key: str = ...) -> Density:
    """Creates a random value that is equal for all coordinates in a world. 
    
    Values are approximately between `a` and `b` and follow a normal distribution
    with a standard deviation of `(b-a) * 1/3`.
    
    **ATTENTION:** Every call to this function produces a new seed-random.
    To use the same seed-random twice without using a transient variable, set the `key` parameter equally.
    """
    # NOTE: The order of a and b is irrelevant
    key = key if key is not ... else str(uuid.uuid4()).replace("-", "")
    if not ":" in key:
        key = "rhombus:generated/" + key
    return a + (b - a) * noise(Noise(1, [1], base_amplitude=1, normalize=True).named(key), xz_scale=0, y_scale=0)