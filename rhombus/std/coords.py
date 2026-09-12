__all__ = [
    "gradient",
    "distance_to_point",
    "find_top_surface",
    "slice",
    "x",
    "z",
    "y",
    "chunk_x",
    "chunk_z",
    "chunk_y",
    "chunk_relative_x",
    "chunk_relative_y",
    "chunk_relative_z",
]

from typing import Literal, Optional

from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro, implementation
from rhombus.std import math, caching
from rhombus.support import vanilla as vt, vanilla_legacy as lt

from ._implementations import unicoords

_coord_limit = 3 * 10**7


# ======// Vanilla Coverage //====================================================================//

@macro
def gradient(
    axis: Literal["x", "y", "z"],
    from_coordinate: int,
    to_coordinate: int,
    from_value: float,
    to_value: float,
    tiling: Literal[
        "extrapolate", "clamp_to_edge", "repeat", "mirrored_repeat"
    ] = "extrapolate",
):
    """Creates a gradient between two coordinates along a given axis.
    
    **NOTE**: In datapack versions before 113 only the Y-axis and the `clamp_to_edge` and `extrapolate` tiling modes can be used.

    Parameters:
        axis (Literal["x", "y", "z"]): The axis along which the gradient is defined.
        from_coordinate (int): The starting coordinate of the gradient.
        to_coordinate (int): The ending coordinate of the gradient.
        from_value (float): The value at the starting coordinate.
        to_value (float): The value at the ending coordinate.
        tiling (Literal["extrapolate", "clamp_to_edge", "repeat", "mirrored_repeat"]): The
            tiling method to use for coordinates outside the gradient range.
    """
    if tiling == "extrapolate":
        m = (to_value - from_value) / (to_coordinate - from_coordinate)
        b = from_value - m * from_coordinate
        from_coordinate, to_coordinate = -_coord_limit, _coord_limit
        from_value, to_value = m * from_coordinate + b, m * to_coordinate + b
        tiling = "clamp_to_edge"
        
    @implementation(until=113)
    def y_clamped_gradient():
        if axis != "y":
            raise NotImplementedError(
                "Cannot provide gradients for the x- and z-axis in datapack versions below 113"
            )
        if tiling != "clamp_to_edge":
            raise NotImplementedError(
                "Cannot provide gradients with tiling other than 'clamp_to_edge' in datapack versions below 113"
            )
        return Density(
            lt.y_clamped_gradient(from_coordinate, to_coordinate, from_value, to_value)
        )
        
    @implementation
    def gradient():
        return Density(
            vt.gradient(axis, tiling, from_coordinate, to_coordinate, from_value, to_value)
        )


def distance_to_point(
    point: tuple[int, int, int],
    metric: Literal[
        "euclidean", "euclidean_squared", "manhattan", "chebyshev"
    ] = "euclidean",
):
    """Returns the distance from the current evaluation context to the specified 3D point.

    Parameters:
        point (tuple[int, int, int]): The absolute (X, Y, Z) coordinates of the target point.
        metric (Literal["euclidean", "euclidean_squared", "manhattan", "chebyshev"]): The
            distance metric to use to calculate the distance.

    ![Visualization](https://minecraft.wiki/images/Distance_to_point_options.png?44fe6)

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#distance_to_point)
    """
    return Density(vt.distance_to_point(point, metric))


@macro
def find_top_surface(
    density: AnyDensity, start: AnyDensity = 320, stop: int = -64, step_size: int = 1
) -> Density:
    """Returns the topmost Y-coordinate where the given `density` evaluates to a value greater than `0`.

    The search starts at the Y-coordinate evaluated by `start` (rounded down to the nearest
    multiple of `step_size`) and steps downwards by `step_size` until it reaches `stop`.
    If a positive density is found during this scan, that Y-coordinate is returned. If no such
    position exists or the start is below `stop`, `stop` is returned.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#find_top_surface)
    """
    return Density(
        vt.find_top_surface(density.AST, upper_bound=start.AST, lower_bound=stop, cell_height=step_size)
    )


@macro
def slice(df: AnyDensity, x: Optional[int] = None, y: Optional[int] = None, z: Optional[int] = None) -> Density:
    """Fixes the coordinate of one or more axes for the given density function.

    When evaluating the resulting density, the specified `x`, `y`, or `z` coordinates will be used
    instead of the context's actual position in the world. This effectively extracts a 2D plane, a
    1D line, or a single point from the original density and projects it continuously along the sliced axes.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#slice)
    """
    out = df.AST
    if x:
        out = vt.slice(input=out, axis="x", coordinate=x)
    if y:
        out = vt.slice(input=out, axis="y", coordinate=y)
    if z:
        out = vt.slice(input=out, axis="z", coordinate=z)
    return Density(out)


# ======// Coordinates //=========================================================================//


def x():
    """Returns the X-coordinate of the current block."""
    @implementation(until=113)
    def x():
        return unicoords.coord_component(
            shift_x=0.99,
            shift_z=1.01,
            quad_shift_x=0.9821958456973294,
            quad_shift_z=0,
        )
    @implementation
    def x():
        return caching.cache(
            gradient(
                "x",
                "clamp_to_edge",
                -_coord_limit,
                _coord_limit,
                -_coord_limit,
                _coord_limit,
            )
        )


def y():
    """Returns the Y-coordinate of the current block."""
    return caching.cache(
        gradient(
            "y",
            "clamp_to_edge",
            -_coord_limit,
            _coord_limit,
            -_coord_limit,
            _coord_limit,
        )
    )


def z():
    """Returns the Z-coordinate of the current block."""
    @implementation(until=113)
    def z():
        return unicoords.coord_component(
            shift_x=1.01,
            shift_z=0.99,
            quad_shift_x=0,
            quad_shift_z=0.9821958456973294,
        )

    @implementation
    def z():
        return caching.cache(
            gradient(
                "z",
                "clamp_to_edge",
                -_coord_limit,
                _coord_limit,
                -_coord_limit,
                _coord_limit,
            )
        )


# ======// Derived Coordinates //================================================================//


def chunk_x():
    """Returns the X-coordinate of the current chunk."""
    return math.floordiv(x(), 16)


def chunk_y():
    """Returns the Y-coordinate of the current chunk."""
    return math.floordiv(y(), 16)


def chunk_z():
    """Returns the Z-coordinate of the current chunk."""
    return math.floordiv(z(), 16)


def chunk_relative_x():
    """Returns the X-coordinate inside of the current chunk."""
    return math.mod(x(), 16)


def chunk_relative_y():
    """Returns the Y-coordinate inside of the current chunk."""
    return math.mod(y(), 16)


def chunk_relative_z():
    """Returns the Z-coordinate inside of the current chunk."""
    return math.mod(z(), 16)
