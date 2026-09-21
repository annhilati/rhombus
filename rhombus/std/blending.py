__all__ = ["beardifier", "blend_alpha", "blend_density", "blend_offset"]


from rhombus.std.density import Density, AnyDensity
from rhombus.std.macros import macro
import rhombus.support.vanilla.types as vt


def beardifier() -> Density:
    """Adds [beards](https://minecraft.wiki/w/Structure_definition) for structures.
    Its value is already added to `final_density` in the noise settings by the game.
    Adding more instances manually increases the beards' size.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#beardifier)
    """
    return Density(vt.beardifier())


def blend_alpha() -> Density:
    """Gets the alpha (weight) value used for blending old and new chunks.

    Returns the blending weight dynamically based on the current position relative to chunks generated in older versions. 
    The value lies within the range `[0.0, 1.0]` and determines how strongly the terrain should interpolate. 
    Far away from old chunk borders, this produces a constant value of `1.0`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#blend_alpha)
    """
    return Density(vt.blend_alpha())


@macro
def blend_density(df: AnyDensity) -> Density:
    """Applies terrain blending transformations to an underlying density function.

    Takes a target density function `df` and modifies its output near the borders of chunks generated in older versions.
    This ensures that terrain features like caves or mountains smoothly transition and stitch together with the old terrain.
    If the current block is not near an old chunk border, this simply returns the unmodified value of the input density function.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#blend_density)
    """
    return Density(vt.blend_density(df.AST))


def blend_offset() -> Density:
    """Gets the height offset used for blending old and new terrain.

    Calculates the positional shift necessary to align new terrain generation with the height of bordering chunks from older versions. 
    This prevents sharp, unnatural cliffs at chunk borders by raising or lowering the terrain appropriately. 
    Far away from old chunk borders, this produces a constant value of `0.0`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#blend_offset)
    """
    return Density(vt.blend_offset())
