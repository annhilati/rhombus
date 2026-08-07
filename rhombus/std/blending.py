from rhombus.std.density import Density, AnyDensity; from rhombus.std.macros import macro
from rhombus.support import vanilla as vt


def beardifier() -> Density[vt.beardifier]:
    """Adds [beards](https://minecraft.wiki/w/Structure_definition) for structures.
    Its value is added to `final_density` in the noise settings by the game.
    Adding more instances manually increases the beards' size.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#beardifier)
    """
    return Density(vt.beardifier())


def blend_alpha() -> Density[vt.blend_alpha]:
    """Used for smooth transition to chunks generated in old versions.

    Returns a constant value of `1.0`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#blend_alpha)
    """
    return Density(vt.blend_alpha())


@macro
def blend_density(argument: AnyDensity) -> Density[vt.blend_density]:
    """Used for smooth transition to chunks generated in old versions.

    Does not affect the density value.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#blend_density)
    """
    return Density(vt.blend_density(argument.AST))


def blend_offset() -> Density[vt.blend_offset]:
    """Used for smooth transition to chunks generated in old versions.

    Returns a constant value of `1.0`.

    ---
    [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#blend_offset)
    """
    return Density(vt.blend_offset())
