from typing import Literal

from rhombus.std import Density, RhombusVersionError, math, caching
from rhombus.core.environment import env
from rhombus.support import vanilla as vt, vanilla_legacy as lt

from ._implementations import unicoords

__all__ = ["gradient", "distance_to_point", "x", "z", "y", "chunk_x", "chunk_z", "chunk_y", "chunk_relative_x", "chunk_relative_y", "chunk_relative_z"]

_coord_limit = 3*10**7


def gradient(axis: Literal["x", "y", "z"], from_coordinate: int, to_coordinate: int, from_value: float, to_value: float, tiling: Literal["extrapolate", "clamp_to_edge", "repeat", "mirrored_repeat"] = "extrapolate"):
    """Creates a gradient between two coordinates along a given axis.
    
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
    if env.datapack_version < 113:
        if axis != "y":
            raise RhombusVersionError("Cannot provide gradients for x- and z-axis in versions below 113")
        if tiling != "clamp_to_edge":
            raise RhombusVersionError("Cannot provide gradients with tiling other than 'clamp_to_edge' in versions below 113")
        return Density(lt.y_clamped_gradient(from_coordinate, to_coordinate, from_value, to_value))
    return Density(vt.gradient(axis, tiling, from_coordinate, to_coordinate, from_value, to_value))


def distance_to_point(point: tuple[int, int, int], metric: Literal["euclidean", "euclidean_squared", "manhattan", "chebyshev"] = "euclidean"):
    return vt.distance_to_point(point, metric)


#======// Coordinates //=========================================================================//


def x():
    """Returns the X-coordinate of the current block.
    """
    if env.datapack_version < 113:
        return unicoords._coord_component(
            shift_x=0.99,
            shift_z=1.01,
            quad_shift_x=0.9821958456973294,
            quad_shift_z=0,
        )
    return caching.cache_once(gradient("x", "clamp_to_edge", -_coord_limit, _coord_limit, -_coord_limit, _coord_limit))



def y():
    """Returns the Y-coordinate of the current block.
        """
    return caching.cache_once(gradient("y", "clamp_to_edge", -_coord_limit, _coord_limit, -_coord_limit, _coord_limit))


def z():
    """Returns the Z-coordinate of the current block.
    """
    if env.datapack_version < 113:
        return unicoords._coord_component(
            shift_x=1.01,
            shift_z=0.99,
            quad_shift_x=0,
            quad_shift_z=0.9821958456973294,
        )
    return caching.cache_once(gradient("z", "clamp_to_edge", -_coord_limit, _coord_limit, -_coord_limit, _coord_limit))


# ======// Derived Coordinates //================================================================//


def chunk_x():
    """Returns the X-coordinate of the current chunk.
    """
    return math.floordiv(x(), 16)


def chunk_y():
    """Returns the Y-coordinate of the current chunk."""
    return math.floordiv(y(), 16)


def chunk_z():
    """Returns the Z-coordinate of the current chunk.
    """
    return math.floordiv(z(), 16)


def chunk_relative_x():
    """Returns the X-coordinate inside of the current chunk.
    """
    return math.mod(x(), 16)


def chunk_relative_y():
    """Returns the Y-coordinate inside of the current chunk."""
    return math.mod(y(), 16)


def chunk_relative_z():
    """Returns the Z-coordinate inside of the current chunk.
    """
    return math.mod(z(), 16)
