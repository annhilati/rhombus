"""Collection of the vanilla density function type.


"""

# For clarification: The functions in this module do not have to exactly mirror the density function t available in vanilla.
#                    The selection of functions provided here should be based on those,
#                    but their implementation may differ if there is a specific way in which they are used in practice.
#                    Example: Caching functions like 'flat_cache' are very often used in separate files to save performance,
#                             so the 'flat_cache' function provided here does not return a 'flat_cache' type Density instance, but a Reference type instance, with a default value.

__all__ = [
    "abs", "add", "beardifier",
    "blend_alpha", "blend_density",
    "blend_offset", "cache_2d",
    "cache_all_in_cell", "cache_once",
    "clamp", "constant", "cube",
    "end_islands", "find_top_surface",
    "flat_cache", "half_negative",
    "interpolated", "interval_select",
    "invert", "max", "min", "mul",
    "noise", "old_blended_noise", 
    "quarter_negative", "range_choice",
    "ref", "shift", "shift_a",
    "shift_b", "shifted_noise",
    "spline", "square", "squeeze",
    "y_clamped_gradient"
]

from rhombus.std.density import Density, AnyDensity
from rhombus.std.noise import Noise
from rhombus.std.macros import macro
from rhombus.std import types

# TODO: return type is not correct for caching functions

#======// Basic Arithmetic //====================================================================//

@macro
def abs(argument: AnyDensity) -> Density[types.abs]:
    """Calculates the absolute value of the input.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#abs)
    """
    return Density(types.abs(argument.AST))

@macro
def add(argument1: AnyDensity, argument2: AnyDensity) -> Density[types.add]:
    """Adds two inputs together.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#add)
    """
    return Density(types.add(argument1.AST, argument2.AST))

@macro
def mul(argument1: AnyDensity, argument2: AnyDensity) -> Density[types.mul]:
    """Multiplies two inputs.
    
    **NOTE** that `Infinity * 0` is `NaN`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#mul)
    """
    return Density(types.mul(argument1.AST, argument2.AST))

@macro
def invert(argument: AnyDensity) -> Density[types.invert]:
    """Calculates `1/x`.
    
    **NOTE** That `invert(0)` is `Infinity`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#invert)
    """
    return Density(types.invert(argument.AST))

@macro
def square(argument: AnyDensity) -> Density[types.square]:
    """Raises the input to the power of 2.
    
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#square)
    """
    return Density(types.square(argument.AST))

@macro
def cube(argument: AnyDensity) -> Density[types.cube]:
    """Raises the input to the power of 3.
    
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#cube)
    """
    return Density(types.cube(argument.AST))

@macro
def half_negative(argument: AnyDensity) -> Density[types.half_negative]:
    """If the input is negative, returns half of the input. Otherwise returns the input.
    
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#half_negative)
    """
    return Density(types.half_negative(argument.AST))

@macro
def quarter_negative(argument: AnyDensity) -> Density[types.quarter_negative]:
    """If the input is negative, returns a quarter of the input. Otherwise returns the input.
    
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#quarter_negative)
    """
    return Density(types.quarter_negative(argument.AST))

@macro
def squeeze(argument: AnyDensity) -> Density[types.squeeze]:
    """First clamps the input between `-1` and `1`, then transforms it using `x/2 - x*x*x/24`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#squeeze)
    """
    return Density(types.squeeze(argument.AST))


#======// Min, Max & Clamping //=================================================================//

@macro
def clamp(input: AnyDensity, min: float, max: float) -> Density[types.clamp]:
    """Returns the larger value from the input and min, and the smaller value from that and max.

    **NOTE** [MC-252814](https://bugs.mojang.com/browse/MC/issues/MC-252814): *Clamp density function takes a direct input and doesn't allow a reference*

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#clamp)
    """
    return Density(types.clamp(input.AST, min, max))

@macro
def max(argument1: AnyDensity, argument2: AnyDensity) -> Density[types.max]:
    """Returns the maximum of two inputs.

    This can be used to combine the terrain masses of two density functions.
    
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#max)
    """
    return Density(types.max(argument1.AST, argument2.AST))

@macro
def min(argument1: AnyDensity, argument2: AnyDensity) -> Density[types.min]:
    """Returns the minimum of two inputs.

    This can be used to combine the cavities of two density functions.
    
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#min)
    """
    return Density(types.min(argument1.AST, argument2.AST))


#======// Flow Control & Selection //============================================================//

@macro
def interval_select(input: AnyDensity, thresholds: list[float], functions: list[AnyDensity]):
    """Selects between a number of density functions based on an input density function and a set of threshold values.

    Parameters:
        input (density function): Density Function, to be compared with given thresholds.
        thresholds (list[float]):  Threshold values to compare input with. Must be non-empty.
            If `input < thresholds[i]`, `functions[i]` will be selected. If the input is greater than the last threshold value, the last function will be selected.
            Must be one fewer thresholds than functions.
        functions (list[density function]): List of density functions to be selected from. Must be one more element in functions than in thresholds.
    
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#interval_select)
    """
    return Density(types.interval_select(input.AST, thresholds, [function.AST for function in functions]))

@macro
def range_choice(input: AnyDensity, min_inclusive: float, max_exclusive: float, when_in_range: AnyDensity, when_out_of_range: AnyDensity) -> Density[types.range_choice]:
    """Computes the input value, and depending on that result returns one of two other density functions. Basically an if-then-else statement.

    **NOTE** To create logic or conditional expressions, use `rhombus.macros.conditional`.

    ```
    if input >= min_inclucive:
        if input < max_exclusive:
            return when_in_range
    return when_out_of_range
    ```
    
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#range_choice)
    """
    return Density(types.range_choice(input.AST, min_inclusive, max_exclusive, when_in_range.AST, when_out_of_range.AST))


#======// Splines & Gradients //=================================================================//

@macro
def spline(coordinate: AnyDensity, points: list[tuple[float, AnyDensity, float]]) -> Density[types.spline]:
    """Computes the value of a cubic spline for the input.

    The values for the points represent in order: `location`, `value` and `derivative`.

    For values beyond the outermost spline points, the value of the nearest spline point is returned.

    **NOTE** If multiple spline points have the same location, for inputs less than the
    location, values aproaching the first defined value will be returned. For
    inputs equal to or greather than the location, values leaving the second
    defined values will be returned. ("first" and "second" refer to the order
    of definition in `points`).

    **NOTE** Approximations for various functions done by splines can be found in `rhombus.macros.smath`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#spline) • [Wikipedia](https://en.wikipedia.org/wiki/Cubic_Hermite_spline)
    """
    points = [(p[0], p[1].AST, p[2]) for p in points]
    return Density(types.spline(coordinate.AST, points))

def y_clamped_gradient(from_y: int, to_y: int, from_value: float, to_value: float) -> Density[types.y_clamped_gradient]:
    """Clamps the Y coordinate between `from_y` and `to_y` and then linearly maps it to a range.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#y_clamped_gradient)
    """
    return Density(types.y_clamped_gradient(from_y, to_y, from_value, to_value))


#======// Noise & World Generation //============================================================//

def beardifier() -> Density[types.beardifier]:
    """Adds [beards](https://minecraft.wiki/w/Structure_definition) for structures.<br>
    Its value is added to `final_density` in the noise settings by the game.
    Adding more instances manually increases the beards' size.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#beardifier)
    """
    return Density(types.beardifier())

def blend_alpha() -> Density[types.blend_alpha]:
    """Used for smooth transition to chunks generated in old versions.

    Returns a constant value of `1.0`.
    
    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#blend_alpha)
    """
    return Density(types.blend_alpha())

@macro
def blend_density(argument: AnyDensity) -> Density[types.blend_density]:
    """Used for smooth transition to chunks generated in old versions.

    Does not affect the density value.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#blend_density)
    """
    return Density(types.blend_density(argument.AST))

def blend_offset() -> Density[types.blend_offset]:
    """Used for smooth transition to chunks generated in old versions.
    
    Returns a constant value of `1.0`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#blend_offset)
    """
    return Density(types.blend_offset())

def end_islands() -> Density[types.end_islands]:
    """Returns a value using a special noise algorithm used for end islands.<br>
    The minimum value is set to `-0.84375`, the maximum value to `0.5625`.
    
    ⚠️ In versions before 1.19, only returns a constant value of `0.0`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#end_islands) -
    [Noise Algorithm Definition](https://mcsrc.dev/#1/26.1-snapshot-1/net/minecraft/world/level/levelgen/DensityFunctions#L565)
    """
    return Density(types.end_islands())

@macro
def find_top_surface(density: AnyDensity, upper_bound: AnyDensity, lower_bound: int, cell_height: int) -> Density[types.find_top_surface]:
    """Scans through a column of a input density and returns the topmost Y-level that is above `0`. If no such position exists withing the bounds, the `lower_bound` is returned.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#find_top_surface)
    """
    return Density(types.find_top_surface(density.AST, upper_bound.AST, lower_bound, cell_height))

def noise(noise: Noise, xz_scale: float = 1, y_scale: float = 1) -> Density[types.noise]:
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

def old_blended_noise(xz_scale: float, y_scale: float, xz_factor: float, y_factor: float, smear_scale_multiplier: float) -> Density[types.old_blended_noise]:
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
    return Density(types.old_blended_noise(xz_scale, y_scale, xz_factor, y_factor, smear_scale_multiplier))

@macro
def shifted_noise(noise: Noise, xz_scale: float, y_scale: float, shift_x: AnyDensity, shift_y: AnyDensity, shift_z: AnyDensity) -> Density[types.shifted_noise]:
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
    return Density(types.shifted_noise(noise, xz_scale, y_scale, shift_x.AST, shift_y.AST, shift_z.AST))


#======// Caching & Interpolation //=============================================================//

@macro
def cache_2d(argument: AnyDensity, *, partition: bool = True) -> Density[types.cache_2d]:
    """Only computes the input density once per horizontal position.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#cache_2d)
    """
    caching_types = (types.cache_2d, types.flat_cache, types.cache_all_in_cell, types.cache_once) # TODO: This should not be hardcoded
    if partition:
        if isinstance(argument.AST, types.Reference) and isinstance(argument.AST.definition, caching_types):
            argument = Density(argument.AST.definition)
        return Density.partitioned(types.cache_2d(argument.AST))
    return Density(types.cache_2d(argument.AST))

@macro
def cache_all_in_cell(argument: AnyDensity, partition: bool = True) -> Density[types.cache_all_in_cell]:
    """🚨 Should not be used in datapacks.

    ---
    
    Used by the game onto `final_density`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#cache_all_in_cell)
    """
    caching_types = (types.cache_2d, types.flat_cache, types.cache_all_in_cell, types.cache_once) # TODO: This should not be hardcoded
    if partition:
        if isinstance(argument.AST, types.Reference) and isinstance(argument.AST.definition, caching_types):
            argument = Density(argument.AST.definition)
        return Density.partitioned(types.cache_all_in_cell(argument.AST))
    return Density(types.cache_all_in_cell(argument.AST))

@macro
def cache_once(argument: AnyDensity, *, partition: bool = True) -> Density[types.cache_once]:
    """If this density function is referenced twice, it is only computed once per block position.

    Does not affect the density value.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#cache_once)
    """
    caching_types = (types.cache_2d, types.flat_cache, types.cache_all_in_cell, types.cache_once) # TODO: This should not be hardcoded
    if partition:
        if isinstance(argument.AST, types.Reference) and isinstance(argument.AST.definition, caching_types):
            argument = Density(argument.AST.definition)
        return Density.partitioned(types.cache_once(argument.AST))
    return Density(types.cache_once(argument.AST))

@macro
def flat_cache(argument: AnyDensity, *, partition: bool = True) -> Density[types.flat_cache]:
    """Calculate the value per 4x4 column (Value at each block in one column is the same). And it is calculated only once per column, at Y=0. Used often in combination with `interpolated`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#flat_cache)
    """
    caching_types = (types.cache_2d, types.flat_cache, types.cache_all_in_cell, types.cache_once) # TODO: This should not be hardcoded
    if partition:
        if isinstance(argument.AST, types.Reference) and isinstance(argument.AST.definition, caching_types):
            argument = Density(argument.AST.definition)
        return Density.partitioned(types.flat_cache(argument.AST))
    return Density(types.flat_cache(argument.AST))

@macro
def interpolated(argument: AnyDensity) -> Density[types.interpolated]:
    """Interpolates at each block in one cell based on the input density function value of some cells around. The size of each cell is 4 by 4. Used often in combination with `flat_cache`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#interpolated)
    """
    return Density(types.interpolated(argument.AST))


#======// Coordinate Shifting //=================================================================//

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


#======// Utility & Misc //======================================================================//

def constant(argument: float) -> Density[types.constant]:
    """Declares a constant float value.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#constant)
    """
    return Density.constant(argument)

def ref(identifier: str, /) -> Density[types.Reference]:
    """References an externally provided density function."""
    return Density.refer(identifier)
