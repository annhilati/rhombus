"""Macros for generating 3D terrain from 2D heightmap data."""

__all__ = ["extrude_heightmap"]


from rhombus.std import Density, AnyDensity, macro
from rhombus.macros import coords

@macro
def extrude_heightmap(heightmap: AnyDensity, map_anchors: tuple[float, float], height_anchors: tuple[float, float]) -> Density:
    """Evaluates a 3D density field by extruding a 2D heightmap along the Y-axis.

    This macro performs a linear remapping of the heightmap values from an
    input range to an output altitude range, then subtracts the current
    Y-coordinate to create a half-space gradient.
    
    **WARNING** This only works if the `heightmap` is truly only
    2-dimensional and returns equal values for all heights.

    Parameters:
        heightmap (density function): 2-dimensional density function representing abstract terrain height.
        map_anchors (tuple[float, float]): Two different values of the heightmap.
        height_anchors (tuple[float, float]): Heights the two `map_anchors` will be mapped to.
    """
    if map_anchors[0] == map_anchors[1] or height_anchors[0] == height_anchors[1]:
        raise ValueError("Anchors must be distinct")
    return (height_anchors[0] + (heightmap - map_anchors[0]) * ((height_anchors[1] - height_anchors[0]) / (map_anchors[1] - map_anchors[0]))) - coords.y()