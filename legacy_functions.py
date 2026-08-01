__all__ = ["slide", "terrain_shaper_spline", "weird_scaled_sampler", "spline"]


from typing import Literal

from rhombus.std.density import Density, AnyDensity
from rhombus.std.noise import Noise
from rhombus.std.macros import macro

from . import legacy


@macro
def slide(argument: AnyDensity) -> Density[legacy.slide]:
    """*Technical description missing*

    Somehow brings values closer to zero. Everything below `Y=7` is `0.117`, everything above `Y=191` is `-0.0781`.
    There are zones between inclusively the heights 7 & 14, 15 & 22 and 183 & 191 where the value strongly differs from the rest and is way more homogenous.

    ---
    ![](data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCA1NDAgMzAwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxzdHlsZT4KICAgIC5ncmF5LXNoYXBlIHsKICAgICAgZmlsbDogI0M2QzZDNjsgLyogTGlnaHQgbW9kZSAqLwogICAgfQoKICAgIEBtZWRpYSAocHJlZmVycy1jb2xvci1zY2hlbWU6IGRhcmspIHsKICAgICAgLmdyYXktc2hhcGUgewogICAgICAgIGZpbGw6ICM1NjU2NTY7IC8qIERhcmsgbW9kZSAqLwogICAgICB9CiAgICB9CiAgPC9zdHlsZT4KICA8cGF0aCBkPSJNMTUwIDBMMjQwIDkwTDIxMCAxMjBMMTIwIDMwTDE1MCAwWiIgZmlsbD0iI0YwOTQwOSIvPgogIDxwYXRoIGQ9Ik00MjAgMzBMNTQwIDE1MEw0MjAgMjcwTDM5MCAyNDBMNDgwIDE1MEwzOTAgNjBMNDIwIDMwWiIgY2xhc3M9ImdyYXktc2hhcGUiLz4KICA8cGF0aCBkPSJNMzMwIDE4MEwzMDAgMjEwTDM5MCAzMDBMNDIwIDI3MEwzMzAgMTgwWiIgZmlsbD0iI0YwOTQwOSIvPgogIDxwYXRoIGQ9Ik0xMjAgMzBMMTUwIDYwTDYwIDE1MEwxNTAgMjQwTDEyMCAyNzBMMCAxNTBMMTIwIDMwWiIgY2xhc3M9ImdyYXktc2hhcGUiLz4KICA8cGF0aCBkPSJNMzkwIDBMNDIwIDMwTDE1MCAzMDBMMTIwIDI3MEwzOTAgMFoiIGZpbGw9IiNGMDk0MDkiLz4KPC9zdmc+)
    `1.18.2-pre1` to `22w11a` ┃ [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#slide)
    """
    return Density(legacy.slide(argument.AST))


@macro
def spline(
    coordinate: AnyDensity,
    points: list[tuple[float, AnyDensity, float]],
    min_value: float,
    max_value: float,
) -> Density[legacy.spline]:
    """Computes the value of a cubic spline for the input.

    The values for the points represent in order: `location`, `value` and `derivative`.

    For values beyond the outermost spline points, the value of the nearest spline point is returned.

    ---
    ![](data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCA1NDAgMzAwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxzdHlsZT4KICAgIC5ncmF5LXNoYXBlIHsKICAgICAgZmlsbDogI0M2QzZDNjsgLyogTGlnaHQgbW9kZSAqLwogICAgfQoKICAgIEBtZWRpYSAocHJlZmVycy1jb2xvci1zY2hlbWU6IGRhcmspIHsKICAgICAgLmdyYXktc2hhcGUgewogICAgICAgIGZpbGw6ICM1NjU2NTY7IC8qIERhcmsgbW9kZSAqLwogICAgICB9CiAgICB9CiAgPC9zdHlsZT4KICA8cGF0aCBkPSJNMTUwIDBMMjQwIDkwTDIxMCAxMjBMMTIwIDMwTDE1MCAwWiIgZmlsbD0iI0YwOTQwOSIvPgogIDxwYXRoIGQ9Ik00MjAgMzBMNTQwIDE1MEw0MjAgMjcwTDM5MCAyNDBMNDgwIDE1MEwzOTAgNjBMNDIwIDMwWiIgY2xhc3M9ImdyYXktc2hhcGUiLz4KICA8cGF0aCBkPSJNMzMwIDE4MEwzMDAgMjEwTDM5MCAzMDBMNDIwIDI3MEwzMzAgMTgwWiIgZmlsbD0iI0YwOTQwOSIvPgogIDxwYXRoIGQ9Ik0xMjAgMzBMMTUwIDYwTDYwIDE1MEwxNTAgMjQwTDEyMCAyNzBMMCAxNTBMMTIwIDMwWiIgY2xhc3M9ImdyYXktc2hhcGUiLz4KICA8cGF0aCBkPSJNMzkwIDBMNDIwIDMwTDE1MCAzMDBMMTIwIDI3MEwzOTAgMFoiIGZpbGw9IiNGMDk0MDkiLz4KPC9zdmc+)
    `1.18.2-pre1` to `1.18.2` ┃ [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#The_legacy_"spline") • [Wikipedia](https://en.wikipedia.org/wiki/Cubic_Hermite_spline)
    """
    points = [(p[0], p[1].AST, p[2]) for p in points]
    return Density(legacy.spline(coordinate.AST, points, min_value, max_value))


@macro
def terrain_shaper_spline(
    spline: Literal["offset", "factor", "jaggedness"],
    min_value: float,
    max_value: float,
    continentalness: AnyDensity,
    erosion: AnyDensity,
    weirdness: AnyDensity,
) -> Density[legacy.terrain_shaper_spline]:
    """Calculate the spline from the noise settings.

    ---
    ![](data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCA1NDAgMzAwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxzdHlsZT4KICAgIC5ncmF5LXNoYXBlIHsKICAgICAgZmlsbDogI0M2QzZDNjsgLyogTGlnaHQgbW9kZSAqLwogICAgfQoKICAgIEBtZWRpYSAocHJlZmVycy1jb2xvci1zY2hlbWU6IGRhcmspIHsKICAgICAgLmdyYXktc2hhcGUgewogICAgICAgIGZpbGw6ICM1NjU2NTY7IC8qIERhcmsgbW9kZSAqLwogICAgICB9CiAgICB9CiAgPC9zdHlsZT4KICA8cGF0aCBkPSJNMTUwIDBMMjQwIDkwTDIxMCAxMjBMMTIwIDMwTDE1MCAwWiIgZmlsbD0iI0YwOTQwOSIvPgogIDxwYXRoIGQ9Ik00MjAgMzBMNTQwIDE1MEw0MjAgMjcwTDM5MCAyNDBMNDgwIDE1MEwzOTAgNjBMNDIwIDMwWiIgY2xhc3M9ImdyYXktc2hhcGUiLz4KICA8cGF0aCBkPSJNMzMwIDE4MEwzMDAgMjEwTDM5MCAzMDBMNDIwIDI3MEwzMzAgMTgwWiIgZmlsbD0iI0YwOTQwOSIvPgogIDxwYXRoIGQ9Ik0xMjAgMzBMMTUwIDYwTDYwIDE1MEwxNTAgMjQwTDEyMCAyNzBMMCAxNTBMMTIwIDMwWiIgY2xhc3M9ImdyYXktc2hhcGUiLz4KICA8cGF0aCBkPSJNMzkwIDBMNDIwIDMwTDE1MCAzMDBMMTIwIDI3MEwzOTAgMFoiIGZpbGw9IiNGMDk0MDkiLz4KPC9zdmc+)
    `1.18.2-pre1` to `1.18.2` ┃ [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#terrain_shaper_spline)
    """
    return Density(
        legacy.terrain_shaper_spline(
            spline,
            min_value,
            max_value,
            continentalness.AST,
            erosion.AST,
            weirdness.AST,
        )
    )


@macro
def weird_scaled_sampler(
    input: AnyDensity, noise: Noise, rarity_value_mapper: Literal["type_1", "type_2"]
) -> Density[legacy.weird_scaled_sampler]:
    """According to the input value, scales and enhances (or weakens) some regions of the specified noise, and then returns the absolute value.

    ---
    ![](data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCA1NDAgMzAwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxzdHlsZT4KICAgIC5ncmF5LXNoYXBlIHsKICAgICAgZmlsbDogI0M2QzZDNjsgLyogTGlnaHQgbW9kZSAqLwogICAgfQoKICAgIEBtZWRpYSAocHJlZmVycy1jb2xvci1zY2hlbWU6IGRhcmspIHsKICAgICAgLmdyYXktc2hhcGUgewogICAgICAgIGZpbGw6ICM1NjU2NTY7IC8qIERhcmsgbW9kZSAqLwogICAgICB9CiAgICB9CiAgPC9zdHlsZT4KICA8cGF0aCBkPSJNMTUwIDBMMjQwIDkwTDIxMCAxMjBMMTIwIDMwTDE1MCAwWiIgZmlsbD0iI0YwOTQwOSIvPgogIDxwYXRoIGQ9Ik00MjAgMzBMNTQwIDE1MEw0MjAgMjcwTDM5MCAyNDBMNDgwIDE1MEwzOTAgNjBMNDIwIDMwWiIgY2xhc3M9ImdyYXktc2hhcGUiLz4KICA8cGF0aCBkPSJNMzMwIDE4MEwzMDAgMjEwTDM5MCAzMDBMNDIwIDI3MEwzMzAgMTgwWiIgZmlsbD0iI0YwOTQwOSIvPgogIDxwYXRoIGQ9Ik0xMjAgMzBMMTUwIDYwTDYwIDE1MEwxNTAgMjQwTDEyMCAyNzBMMCAxNTBMMTIwIDMwWiIgY2xhc3M9ImdyYXktc2hhcGUiLz4KICA8cGF0aCBkPSJNMzkwIDBMNDIwIDMwTDE1MCAzMDBMMTIwIDI3MEwzOTAgMFoiIGZpbGw9IiNGMDk0MDkiLz4KPC9zdmc+)
    `1.18.2-pre1` to `26.2-snap4` ┃ [Minecraft Wiki Reference](https://minecraft.wiki/w/Density_function#weird_scaled_sampler)
    """
    return Density(legacy.weird_scaled_sampler(input.AST, noise, rarity_value_mapper))
