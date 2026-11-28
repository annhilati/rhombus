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
    "weird_scaled_sampler",
    "cellular_noise"
]

from typing import Literal
import uuid
import math as py_math

from rhombus.core import fields
from rhombus.library.vanilla import types as vt, legacy_types as lt
from rhombus.std.builtin.density import Density, AnyDensity
from rhombus.std.builtin.macros import macro, implementation
from rhombus.std.builtin.dsl_config import DSLConfig, field
from rhombus.std import caching, math, conditional
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
    identifier: str | None = field(default=None, init=False)
    
    
    @classmethod
    def refer(cls, identifier: str) -> Noise:
        # TODO: Standardize refering and naming for DSLConfig 
        identifier = "minecraft:" + identifier if not ":" in identifier else identifier
        instance = Noise(base_octave=None, amplitudes=None, base_amplitude=None, normalize=None)
        instance.identifier = identifier
        return instance
    
    def named(self, identifier: str) -> Noise:
        identifier = "minecraft:" + identifier if not ":" in identifier else identifier
        self.identifier = identifier
        return self


    def build(self) -> vt.NoiseDefinition:
        
        if self.identifier is not None:
            if all(v is None for k, v in fields(self).items() if k != "identifier"):
                return vt.NoiseDefinition.refer(self.identifier)
            identifier, self.identifier = self.identifier, None
            return self.build().named(identifier)
        
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
        inner = (math.clamp(100.0 - dist, min=-100.0, max=80.0) - 8.0) * (1 / 128)
        inner_slice = slice(inner, y=0)
            
        return math.max(inner_slice, end_outer_islands())
    
    
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
def random(a: AnyDensity = 0, b: AnyDensity = 1, *, uniform: bool = True, key: str = ...) -> Density:
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
    
    if uniform:
        # The noise's values are distributed normally with a standard deviation of 1/3.
        # We perform Inverse Transform Sampling to redistribute the random values uniformly.
        return a + (b - a) * (1/2 + (math.distributions.erf(3/sqrt2 * n)) / (2 * py_math.erf(3/sqrt2)))
    return a + (b - a) * (0.5 * n + 0.5)


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
    return a + (b - a) * noise(Noise(1, [1], base_amplitude=1, normalize=True).named(key), xz_scale=0, y_scale=0)#


# ======// Cellular Noise //=====================================================================//


# Original implementation by Annhilati
@macro
def cellular_noise(
    scale: int = 32,
    *,
    dim: Literal["xz", "xyz"] = "xz",
    return_type: Literal["distance", "value"] = "value",
    jitter: float = 0.9,
    upscale_cell_size: int = 1,
) -> Density:
    """Samples a jittered Worley / Voronoi Noise.

    Parameters:
        scale (int): Average diameter of a cell.
        dim ("xz" | "xyz"): Whether to sample the noise only on the horizontal plane or in all three dimensions.
        return_type ("distance" | "value"): Whether the sampled value is the distance to the cell center or the cell's value.
        jitter (float between 0 and 1): What portion of the scale cell centers can deviate.
        upscale_cell_size (int): Reduces the number of samples to increase performance, but in trade for precision.
    """
    from rhombus.std import coords # avoid circular import

    if not 0 <= jitter <= 1:
        raise ValueError("Jitter has to be betweeen 0 and 1")

    max_jitter = (scale / 2) * jitter

    # deactivate uniform to save performance
    jx_noise  = random(-1, 1, uniform=False)
    jz_noise  = random(-1, 1, uniform=False)
    jy_noise  = random(-1, 1, uniform=False) # only needed if dim == 3
    val_noise = random(-1, 1, uniform=False) # only needed if return_type == "value"

    def nn_upscale(df: Density, cx: int, cy: int, cz: int) -> Density:
        if cx == 1 and cy == 1 and cz == 1:
            return df
        return caching.upscale(
            df,
            x_cell_size=cx,
            y_cell_size=cy,
            z_cell_size=cz,
            x_mode="nearest_neighbor",
            y_mode="nearest_neighbor",
            z_mode="nearest_neighbor",
        )

    # Lossless upscale cell size: any divisor of both d and 16 never crosses a grid or chunk boundary
    cell_xz = py_math.gcd(scale, 16)
    cell_y = 64 if dim == "xz" else py_math.gcd(scale, 16)

    # Cached coordinates (~30 reuses per block)
    coords_cached = math.linalg.DensityVector(
        caching.cache(coords.x()),
        caching.cache(coords.y()) if dim == "xyz" else 0,
        caching.cache(coords.z()),
    )
    
    def get_jitter(n: Density, cx: AnyDensity, cy: AnyDensity, cz: AnyDensity) -> Density:
        # No `cache()` inside `domain_pin`: `domain_pin` (`minecraft:domain_warp`) samples
        # its input at a warped context; wrapping the inner `noise(n)` in `cache()` is  
        # counterproductive and can cause stale cache hits. Partitioning/caching belongs
        # on the outer shared nodes (`base_*`, `dist_sq`, `min_dist_sq`, `val`).
        raw = coords.domain_pin(n, x=cx, y=cy, z=cz)
        return nn_upscale(math.clamp(raw * 2.5, -1.0, 1.0) * max_jitter, cell_xz, cell_y, cell_xz)

    # Pre-partition cell origins so all 9 / 27 neighbor lookups share the floor division
    base = coords_cached.map(lambda vc: Density.partitioned(nn_upscale((vc // scale) * scale, cell_xz, cell_y, cell_xz)))

    distances_sq: list[Density] = []
    cell_values: list[Density] = []

    if dim == "xz":
        for i in (-1, 0, 1):
            for k in (-1, 0, 1):

                center = base.xz + math.linalg.DensityVector(
                    i * scale + scale / 2,
                    k * scale + scale / 2,
                )

                dj = math.linalg.DensityVector(
                    get_jitter(jx_noise, center.u, 0, center.v),
                    get_jitter(jz_noise, center.u, 0, center.v),
                )

                delta = center + dj - coords_cached.xz

                # Squared Euclidean distance avoids sqrt in min(); cache for min() + equals()
                dist_sq = Density.partitioned(caching.cache(delta.u ** 2 + delta.v ** 2))
                distances_sq.append(dist_sq)

                if return_type == "value":
                    val = nn_upscale(coords.domain_pin(val_noise, x=center.u, y=0, z=center.v), cell_xz, cell_y, cell_xz)
                    cell_values.append(Density.partitioned(val))
                    
    else:
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for k in (-1, 0, 1):

                    center = base + math.linalg.DensityVector(
                        i * scale + scale / 2,
                        j * scale + scale / 2,
                        k * scale + scale / 2,
                    )
                    
                    dj = math.linalg.DensityVector(
                        get_jitter(jx_noise, center.x, center.y, center.z),
                        get_jitter(jy_noise, center.x, center.y, center.z),
                        get_jitter(jz_noise, center.x, center.y, center.z),
                    )

                    delta = center + dj - coords_cached

                    # Squared Euclidean distance avoids sqrt in min(); cache for min() + equals()
                    dist_sq = Density.partitioned(caching.cache(delta.x ** 2 + delta.y ** 2 + delta.z ** 2))
                    distances_sq.append(dist_sq)

                    if return_type == "value":
                        val = nn_upscale(coords.domain_pin(val_noise, x=center.x, y=center.y, z=center.z), cell_xz, cell_y, cell_xz)
                        cell_values.append(Density.partitioned(val))

    min_dist_sq = Density.partitioned(caching.cache(math.min(*distances_sq)))

    if return_type == "distance":
        # Normalized Worley distance (0 at center, ~1 at borders)
        res = math.sqrt(min_dist_sq) / (scale / 2)
    else:
        # Skip the final comparison by using the last cell as .otherwise() fallback
        cond = conditional.when(1).equals(0).then(0)
        for dist_sq, val in zip(distances_sq[:-1], cell_values[:-1]):
            cond.elsewhen(dist_sq).equals(min_dist_sq).then(val)
        res = cond.otherwise(cell_values[-1])

    out_y_cell = 64 if dim == "xz" else upscale_cell_size
    if upscale_cell_size > 1 or dim == "xz":
        res = nn_upscale(res, upscale_cell_size, out_y_cell, upscale_cell_size)

    return res