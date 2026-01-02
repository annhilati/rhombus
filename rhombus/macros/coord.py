"""Macros for reconstructing the coordinates of the block being evaluated.

The techniques used were invented by *Uni* aka. *unnecessarymb*.<br> An original JSON-implementation of it can be seen at [klinbee/One-Island/.../one_island/worldgen/density_function/coord](https://github.com/klinbee/One-Island/tree/main/One_Survival_Island/data/one_island/worldgen/density_function/coord).

---

# Technical Explanation

### Background
To patch the Far Lands, Mojang modified noise evaluation so that extremely large inputs
*wrap around* instead of diverging. Internally, this wraparound is triggered by loss of
floating-point precision at very large magnitudes.

### Core idea
We deliberately scale a noise input to such an extreme magnitude that the wraparound
behavior becomes predictable. By doing so, the noise enters a regime where flipping the
lowest bits of the floating-point representation causes the value to alternate between
two stable states:
- one where the noise wraps to a large value
- one where it effectively wraps to zero

This creates a binary signal that can be detected and reused.

### Stripe construction
A second modulo operation is applied, but only *after* adding an offset. Because floating-
point rounding occurs at multiple internal stages, the same mathematical value may round
differently depending on where the precision loss happens. This produces repeating
intervals (“stripes”) in space.

Each stripe has twice the width of the previous one. By stacking these stripes and
conditionally inverting the accumulated result at each scale, then adding a constant,
we can compose increasingly coarse positional information. Conceptually, this is the
inverse of building a triangle wave from absolute-value functions.

### Recovering the sign
To distinguish positive from negative coordinates, we sample the noise at even higher
magnitudes. Beyond a certain threshold, the Far Lands fix breaks down completely and the
noise returns effectively garbage values.

By carefully aligning the noise offset, this breakdown point can be positioned exactly
on the plane dividing the world into hemispheres. The resulting discontinuity provides
reliable sign information for the coordinate.

### Result
Through controlled exploitation of floating-point wraparound, precision loss, and
conditional composition, this macro reconstructs the coordinates using only vanilla
density functions.
"""

import rhombus
from rhombus.language import builtins as f

_coord_stripe_noise = rhombus.Noise(87, [1])
_coord_quad_noise = rhombus.Noise(88, [1])
_coord_base = f.flat_cache(f.cache_2d(-1 * f.shifted_noise(noise=_coord_stripe_noise, xz_scale=2**-52, y_scale=0, shift_x=1.01, shift_y=0, shift_z=1.01)))


#======// Additional Information about the Implementation //=====================================//
#   Why are the nested multiplications exactly 27 (26 when leaving the coord_quad-sampling out) arguments long?
#       2^26 is the smallest power of two that’s wider then a Minecraft world
#   Why are the 5 outermost powers of two calculated by a density function and not given literal?
#       Minecraft doesn’t allow literals over 1 million


# Differences between the two: shift_x and shift_z are swapped in every shifted_noise-sampler

def x():
    """Returns the X-coordinate of the block being evaluated.
    
    This macro works by utilizing float precision loss at extremely small noise scales. It is pretty resource-intensive.<br>
    For more information on how it works read the docstring of `rhombus.macro.coord`.
    """
    innermost = f.range_choice(input=(_coord_base + f.shifted_noise(noise=_coord_stripe_noise, xz_scale=2**-55, y_scale=0, shift_x=0.99, shift_y=0, shift_z=1.01)), min_inclusive=0.0, max_exclusive=5e-324, when_in_range=1.0, when_out_of_range=0.0)

    x = innermost
    for i in range(25):
        x = f.add(
            argument1=2**i if 2**i < 1_000_000 else (f.mul(65536.0, 2**i / 65536.0 if i != 24 else -2**i / 65536.0)),
            argument2=f.mul(
                argument1=f.range_choice(input=(_coord_base + f.shifted_noise(noise=_coord_stripe_noise, xz_scale=2**(-56-i), y_scale=0, shift_x=0.99, shift_y=0, shift_z=1.01)), min_inclusive=0.0, max_exclusive=5e-324, when_in_range=1.0, when_out_of_range=-1.0),
                argument2=x
        ))

    outermost_mul = f.mul(
        argument1=f.range_choice(input=f.shifted_noise(noise=_coord_quad_noise, xz_scale=2**-25, y_scale=0, shift_x=0.9821958456973294, shift_y=0, shift_z=0), min_inclusive=-2.0, max_exclusive=2.0, when_in_range=-4.0, when_out_of_range=4.0),
        argument2=x
    )

    return f.interpolated(f.flat_cache(f.cache_2d(outermost_mul)))

def z():
    """Returns the Z-coordinate of the block being evaluated.
    
    This macro works by utilizing float precision loss at extremely small noise scales. It is pretty resource-intensive.<br>
    For more information on how it works read the docstring of `rhombus.macro.coord`.
    """
    innermost = f.range_choice(input=(_coord_base + f.shifted_noise(noise=_coord_stripe_noise, xz_scale=2**-55, y_scale=0, shift_x=1.01, shift_y=0, shift_z=0.99)), min_inclusive=0.0, max_exclusive=5e-324, when_in_range=1.0, when_out_of_range=0.0)

    x = innermost
    for i in range(25):
        x = f.add(
            argument1=2**i if 2**i < 1_000_000 else (f.mul(65536.0, 2**i / 65536.0 if i != 24 else -2**i / 65536.0)),
            argument2=f.mul(
                argument1=f.range_choice(input=(_coord_base + f.shifted_noise(noise=_coord_stripe_noise, xz_scale=2**(-56-i), y_scale=0, shift_x=1.01, shift_y=0, shift_z=0.99)), min_inclusive=0.0, max_exclusive=5e-324, when_in_range=1.0, when_out_of_range=-1.0),
                argument2=x
        ))

    outermost_mul = f.mul(
        argument1=f.range_choice(input=f.shifted_noise(noise=_coord_quad_noise, xz_scale=2**-25, y_scale=0, shift_x=0, shift_y=0, shift_z=0.9821958456973294), min_inclusive=-2.0, max_exclusive=2.0, when_in_range=-4.0, when_out_of_range=4.0),
        argument2=x
    )

    return f.interpolated(f.flat_cache(f.cache_2d(outermost_mul)))