from rhombus.std import noise, math, caching

from ._implementations import unicoords

__all__ = ["x", "z", "y", "chunk_x", "chunk_z", "chunk_y", "chunk_relative_x", "chunk_relative_y", "chunk_relative_z"]


def x():
    """Returns the X-coordinate of the current block.
    """
    return unicoords._coord_component(
        shift_x=0.99,
        shift_z=1.01,
        quad_shift_x=0.9821958456973294,
        quad_shift_z=0,
    )


def y():
    """Returns the Y-coordinate of the current block.
        """
    return caching.cache_once(y_clamped_gradient(-4062, 4062, -4062, 4062))


def z():
    """Returns the Z-coordinate of the current block.
    """
    return unicoords._coord_component(
        shift_x=1.01,
        shift_z=0.99,
        quad_shift_x=0,
        quad_shift_z=0.9821958456973294,
    )


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
