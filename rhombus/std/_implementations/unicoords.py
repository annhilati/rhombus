"""Macros for reconstructing the coordinates of the block being evaluated.

The techniques used here were invented by *Uni* aka. *unnecessarymb*.<br>
An original JSON-implementation can be seen [here](https://github.com/klinbee/One-Island/tree/main/One_Survival_Island/data/one_island/worldgen/density_function/coord).

---

## Technical Explanation

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

from rhombus.std.math import mul, add
from rhombus.std.conditional import range_choice
from rhombus.std.noise import Noise, shifted_noise
from rhombus.std.caching import flat_cache, cache_2d, interpolated, recurrence_cache


_coord_stripe_noise = Noise(78, [1])
_coord_quad_noise = Noise(88, [1])
_coord_base = flat_cache(
    cache_2d(
        -1
        * shifted_noise(
            noise=_coord_stripe_noise,
            xz_scale=2**-52,
            y_scale=0,
            shift_x=1.01,
            shift_y=0,
            shift_z=1.01,
        )
    )
)


# ======// Additional Information about the Implementation //=====================================//
#   Why are the nested multiplications exactly 27 (26 when leaving the coord_quad-sampling out) arguments long?
#       2^26 is the smallest power of two that’s wider then a Minecraft world
#   Why are the 5 outermost powers of two calculated by a density function and not given literal?
#       Minecraft doesn’t allow literals over 1 million


def coord_component(
    shift_x: float, shift_z: float, quad_shift_x: float, quad_shift_z: float
):
    innermost = range_choice(
        input=(
            _coord_base
            + shifted_noise(
                noise=_coord_stripe_noise,
                xz_scale=2**-55,
                y_scale=0,
                shift_x=shift_x,
                shift_y=0,
                shift_z=shift_z,
            )
        ),
        min_inclusive=0.0,
        max_exclusive=5e-324,
        when_in_range=1.0,
        when_out_of_range=0.0,
    )

    value = innermost
    for i in range(25):
        value = add(
            argument1=2**i
            if 2**i < 1_000_000
            else (mul(65536.0, 2**i / 65536.0 if i != 24 else -(2**i) / 65536.0)),
            argument2=mul(
                argument1=range_choice(
                    input=(
                        _coord_base
                        + shifted_noise(
                            noise=_coord_stripe_noise,
                            xz_scale=2 ** (-56 - i),
                            y_scale=0,
                            shift_x=shift_x,
                            shift_y=0,
                            shift_z=shift_z,
                        )
                    ),
                    min_inclusive=0.0,
                    max_exclusive=5e-324,
                    when_in_range=1.0,
                    when_out_of_range=-1.0,
                ),
                argument2=value,
            ),
        )

    outermost_mul = mul(
        argument1=range_choice(
            input=shifted_noise(
                noise=_coord_quad_noise,
                xz_scale=2**-25,
                y_scale=0,
                shift_x=quad_shift_x,
                shift_y=0,
                shift_z=quad_shift_z,
            ),
            min_inclusive=-2.0,
            max_exclusive=2.0,
            when_in_range=-4.0,
            when_out_of_range=4.0,
        ),
        argument2=value,
    )

    return recurrence_cache(interpolated(flat_cache(cache_2d(outermost_mul))), max_nodes=4)
